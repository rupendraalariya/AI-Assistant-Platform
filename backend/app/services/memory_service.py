"""Memory Service - Adaptive conversation memory with fallback hierarchy.

Fallback order:
1. Redis (fast, distributed) - if available
2. In-Memory Python dict (always works, lost on restart)

The service never crashes regardless of Redis availability.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.config import get_settings
from app.db.redis import get_redis, is_redis_available
from app.utils.logger import get_logger
from app.utils.token_counter import count_tokens

logger = get_logger(__name__)
settings = get_settings()

# Memory configuration
MAX_BUFFER_TURNS = 5
MAX_TOKEN_BUDGET = 4000
SUMMARY_TRIGGER_TURNS = 16


# ============================================================
# MEMORY PROVIDERS (Strategy Pattern)
# ============================================================


class MemoryProvider(ABC):
    """Abstract base for memory storage backends."""

    @abstractmethod
    async def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get all messages for a session."""
        ...

    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session history."""
        ...

    @abstractmethod
    async def get_summary(self, session_id: str) -> Optional[str]:
        """Get conversation summary."""
        ...

    @abstractmethod
    async def save_summary(self, session_id: str, summary: str) -> None:
        """Save conversation summary."""
        ...

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Clear all memory for a session."""
        ...

    @abstractmethod
    async def get_message_count(self, session_id: str) -> int:
        """Get message count for a session."""
        ...


class RedisMemoryProvider(MemoryProvider):
    """Redis-backed memory provider for production use."""

    def _messages_key(self, session_id: str) -> str:
        return f"session:{session_id}:messages"

    def _summary_key(self, session_id: str) -> str:
        return f"session:{session_id}:summary"

    async def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        redis = await get_redis()
        if not redis:
            return []
        try:
            raw = await redis.lrange(self._messages_key(session_id), 0, -1)
            return [json.loads(msg) for msg in raw]
        except Exception as e:
            logger.warning("Redis get_messages failed", error=str(e))
            return []

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        redis = await get_redis()
        if not redis:
            return
        try:
            message = json.dumps({"role": role, "content": content})
            await redis.rpush(self._messages_key(session_id), message)
            await redis.expire(self._messages_key(session_id), settings.redis_ttl)
        except Exception as e:
            logger.warning("Redis add_message failed", error=str(e))

    async def get_summary(self, session_id: str) -> Optional[str]:
        redis = await get_redis()
        if not redis:
            return None
        try:
            return await redis.get(self._summary_key(session_id))
        except Exception:
            return None

    async def save_summary(self, session_id: str, summary: str) -> None:
        redis = await get_redis()
        if not redis:
            return
        try:
            await redis.set(self._summary_key(session_id), summary)
            await redis.expire(self._summary_key(session_id), settings.redis_ttl)
        except Exception as e:
            logger.warning("Redis save_summary failed", error=str(e))

    async def clear(self, session_id: str) -> None:
        redis = await get_redis()
        if not redis:
            return
        try:
            await redis.delete(
                self._messages_key(session_id),
                self._summary_key(session_id),
            )
        except Exception:
            pass

    async def get_message_count(self, session_id: str) -> int:
        redis = await get_redis()
        if not redis:
            return 0
        try:
            return await redis.llen(self._messages_key(session_id))
        except Exception:
            return 0


class LocalMemoryProvider(MemoryProvider):
    """In-memory dictionary provider. Always works, no external deps."""

    def __init__(self):
        self._store: Dict[str, List[Dict[str, str]]] = {}
        self._summaries: Dict[str, str] = {}

    async def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        return self._store.get(session_id, []).copy()

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append({"role": role, "content": content})

    async def get_summary(self, session_id: str) -> Optional[str]:
        return self._summaries.get(session_id)

    async def save_summary(self, session_id: str, summary: str) -> None:
        self._summaries[session_id] = summary

    async def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)
        self._summaries.pop(session_id, None)

    async def get_message_count(self, session_id: str) -> int:
        return len(self._store.get(session_id, []))


# ============================================================
# MEMORY MANAGER (Facade with automatic provider selection)
# ============================================================

# Singleton local provider (persists across requests within same process)
_local_provider = LocalMemoryProvider()


class MemoryManager:
    """Manages conversation memory with automatic fallback.

    Selects the best available provider:
    1. Redis (if available)
    2. In-memory dict (always available)
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._provider: Optional[MemoryProvider] = None

    @property
    def provider(self) -> MemoryProvider:
        """Get the active memory provider with fallback logic."""
        if is_redis_available():
            return RedisMemoryProvider()
        return _local_provider

    async def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        try:
            await self.provider.add_message(self.session_id, role, content)
        except Exception as e:
            # Ultimate fallback - store locally
            logger.warning("Memory add_message failed, using local fallback", error=str(e))
            await _local_provider.add_message(self.session_id, role, content)

    async def get_context(self) -> List[Dict[str, str]]:
        """Get conversation context using adaptive strategy."""
        try:
            messages = await self.provider.get_messages(self.session_id)
        except Exception as e:
            logger.warning("Memory get_context failed", error=str(e))
            messages = await _local_provider.get_messages(self.session_id)

        if not messages:
            return []

        turn_count = len(messages) // 2

        if turn_count <= MAX_BUFFER_TURNS:
            return messages
        elif turn_count < SUMMARY_TRIGGER_TURNS:
            return self._token_aware_trim(messages)
        else:
            return await self._with_summary(messages)

    def _token_aware_trim(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Keep most recent messages within token budget."""
        total_tokens = 0
        trimmed = []
        for msg in reversed(messages):
            msg_tokens = count_tokens(msg["content"])
            if total_tokens + msg_tokens > MAX_TOKEN_BUDGET:
                break
            trimmed.insert(0, msg)
            total_tokens += msg_tokens
        return trimmed

    async def _with_summary(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepend summary to recent messages."""
        summary = await self.provider.get_summary(self.session_id)
        recent = messages[-10:]
        if summary:
            context = [{"role": "system", "content": f"Previous conversation summary: {summary}"}]
            context.extend(recent)
            return context
        return recent

    async def save_summary(self, summary: str) -> None:
        """Save a conversation summary."""
        try:
            await self.provider.save_summary(self.session_id, summary)
        except Exception:
            await _local_provider.save_summary(self.session_id, summary)

    async def get_message_count(self) -> int:
        """Get total message count."""
        try:
            return await self.provider.get_message_count(self.session_id)
        except Exception:
            return await _local_provider.get_message_count(self.session_id)

    async def should_summarize(self) -> bool:
        """Check if conversation needs summarization."""
        count = await self.get_message_count()
        return count >= SUMMARY_TRIGGER_TURNS * 2

    async def get_all_messages(self) -> List[Dict[str, str]]:
        """Get all messages for summarization."""
        try:
            return await self.provider.get_messages(self.session_id)
        except Exception:
            return await _local_provider.get_messages(self.session_id)

    async def clear(self) -> None:
        """Clear all memory for this session."""
        try:
            await self.provider.clear(self.session_id)
        except Exception:
            pass
        # Always clear local too
        await _local_provider.clear(self.session_id)


# ============================================================
# PUBLIC API
# ============================================================


def get_memory_service(session_id: str) -> MemoryManager:
    """Factory function - returns a MemoryManager for the given session."""
    return MemoryManager(session_id=session_id)
