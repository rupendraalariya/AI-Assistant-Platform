"""Redis connection management - fully optional with graceful degradation."""

from typing import Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global Redis client - None means unavailable
_redis_client = None
_redis_available: bool = False


def is_redis_available() -> bool:
    """Check if Redis is currently available."""
    return _redis_available


async def get_redis():
    """Get Redis client instance. Returns None if Redis is unavailable."""
    global _redis_client, _redis_available
    if not _redis_available:
        return None
    return _redis_client


async def init_redis() -> None:
    """Initialize Redis connection. Never raises - sets availability flag."""
    global _redis_client, _redis_available

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        await client.ping()
        _redis_client = client
        _redis_available = True
        logger.info("Redis connection established successfully")
    except ImportError:
        _redis_available = False
        logger.warning("Redis package not installed. Running without Redis.")
    except Exception as e:
        _redis_available = False
        _redis_client = None
        logger.warning(
            "Redis unavailable, using fallback memory storage",
            error=str(e),
        )


async def close_redis() -> None:
    """Close Redis connection if it exists."""
    global _redis_client, _redis_available
    if _redis_client and _redis_available:
        try:
            await _redis_client.close()
            logger.info("Redis connection closed")
        except Exception:
            pass
    _redis_client = None
    _redis_available = False
