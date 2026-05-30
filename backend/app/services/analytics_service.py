"""Analytics Service - Usage tracking and metrics."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.session import Session
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for tracking and reporting usage analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_usage(self, user_id: UUID) -> Dict:
        """Get usage statistics for a specific user."""
        # Total sessions
        sessions_result = await self.db.execute(
            select(func.count(Session.id)).where(Session.user_id == user_id)
        )
        total_sessions = sessions_result.scalar() or 0

        # Total messages
        messages_result = await self.db.execute(
            select(func.count(Chat.id)).where(Chat.user_id == user_id)
        )
        total_messages = messages_result.scalar() or 0

        # Total tokens
        tokens_result = await self.db.execute(
            select(func.sum(Chat.tokens_used)).where(Chat.user_id == user_id)
        )
        total_tokens = tokens_result.scalar() or 0

        # Total cost
        cost_result = await self.db.execute(
            select(func.sum(Session.total_cost)).where(Session.user_id == user_id)
        )
        total_cost = cost_result.scalar() or Decimal("0")

        # Average latency
        latency_result = await self.db.execute(
            select(func.avg(Chat.latency_ms)).where(
                Chat.user_id == user_id,
                Chat.role == "assistant",
            )
        )
        avg_latency = latency_result.scalar() or 0

        return {
            "user_id": str(user_id),
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "total_cost": float(total_cost),
            "avg_latency_ms": round(float(avg_latency), 2),
        }

    async def get_system_metrics(self) -> Dict:
        """Get system-wide analytics (admin only)."""
        # Active users (users with activity in last 7 days)
        active_users_result = await self.db.execute(
            select(func.count(func.distinct(Chat.user_id)))
        )
        active_users = active_users_result.scalar() or 0

        # Total conversations
        total_sessions_result = await self.db.execute(
            select(func.count(Session.id))
        )
        total_sessions = total_sessions_result.scalar() or 0

        # Total tokens used
        total_tokens_result = await self.db.execute(
            select(func.sum(Chat.tokens_used))
        )
        total_tokens = total_tokens_result.scalar() or 0

        # Total cost
        total_cost_result = await self.db.execute(
            select(func.sum(Session.total_cost))
        )
        total_cost = total_cost_result.scalar() or Decimal("0")

        # Average response time
        avg_latency_result = await self.db.execute(
            select(func.avg(Chat.latency_ms)).where(Chat.role == "assistant")
        )
        avg_latency = avg_latency_result.scalar() or 0

        # Total registered users
        total_users_result = await self.db.execute(
            select(func.count(User.id))
        )
        total_users = total_users_result.scalar() or 0

        return {
            "active_users": active_users,
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "total_cost": float(total_cost),
            "avg_latency_ms": round(float(avg_latency), 2),
        }

    async def track_chat_metrics(
        self,
        session_id: UUID,
        tokens_used: int,
        cost: float,
    ) -> None:
        """Update session metrics after a chat interaction."""
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.total_tokens += tokens_used
            session.total_cost += Decimal(str(cost))
            await self.db.flush()
