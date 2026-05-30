"""Cost Optimization Service - Token tracking, prompt compression, and cost management."""

from typing import Dict, List, Optional

from app.utils.logger import get_logger
from app.utils.token_counter import count_tokens, estimate_cost

logger = get_logger(__name__)

# Token budgets
MAX_CONTEXT_TOKENS = 4000
MAX_PROMPT_TOKENS = 8000


class CostService:
    """Service for cost optimization and token management."""

    def compress_context(
        self,
        context: str,
        max_tokens: int = MAX_CONTEXT_TOKENS,
    ) -> str:
        """Compress RAG context to fit within token budget.

        Uses sentence-level trimming to keep most relevant content.
        """
        current_tokens = count_tokens(context)
        if current_tokens <= max_tokens:
            return context

        # Split into sentences and trim from the end
        sentences = context.split(". ")
        compressed = []
        token_count = 0

        for sentence in sentences:
            sentence_tokens = count_tokens(sentence)
            if token_count + sentence_tokens > max_tokens:
                break
            compressed.append(sentence)
            token_count += sentence_tokens

        return ". ".join(compressed)

    def trim_chat_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = MAX_CONTEXT_TOKENS,
    ) -> List[Dict[str, str]]:
        """Trim chat history to fit within token budget.

        Keeps most recent messages, removes oldest first.
        """
        total_tokens = sum(count_tokens(m["content"]) for m in messages)

        if total_tokens <= max_tokens:
            return messages

        # Remove oldest messages until within budget
        trimmed = list(messages)
        while total_tokens > max_tokens and len(trimmed) > 2:
            removed = trimmed.pop(0)
            total_tokens -= count_tokens(removed["content"])

        return trimmed

    def calculate_session_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4o-mini",
    ) -> Dict:
        """Calculate cost breakdown for a session interaction."""
        cost = estimate_cost(prompt_tokens, completion_tokens, model)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost,
            "model": model,
        }

    def get_optimization_suggestions(
        self,
        total_tokens: int,
        avg_tokens_per_message: float,
        session_count: int,
    ) -> List[str]:
        """Generate cost optimization suggestions."""
        suggestions = []

        if avg_tokens_per_message > 500:
            suggestions.append(
                "Consider enabling prompt compression to reduce average token usage"
            )

        if total_tokens > 100000:
            suggestions.append(
                "High token usage detected. Consider using gpt-4o-mini for routine queries"
            )

        if session_count > 50:
            suggestions.append(
                "Many active sessions. Enable automatic summarization to reduce memory costs"
            )

        return suggestions


def get_cost_service() -> CostService:
    """Factory function for cost service."""
    return CostService()
