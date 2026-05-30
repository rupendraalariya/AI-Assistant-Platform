"""Analytics endpoints - usage metrics and cost tracking."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_admin_user, get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/usage")
async def get_user_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics for the current user."""
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_user_usage(current_user.id)


@router.get("/system")
async def get_system_metrics(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide metrics (admin only)."""
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_system_metrics()


@router.get("/costs")
async def get_cost_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get cost breakdown for the current user."""
    analytics_service = AnalyticsService(db)
    usage = await analytics_service.get_user_usage(current_user.id)

    return {
        "user_id": str(current_user.id),
        "total_cost": usage["total_cost"],
        "total_tokens": usage["total_tokens"],
        "total_sessions": usage["total_sessions"],
        "cost_per_session": (
            usage["total_cost"] / usage["total_sessions"]
            if usage["total_sessions"] > 0
            else 0
        ),
        "avg_tokens_per_message": (
            usage["total_tokens"] / usage["total_messages"]
            if usage["total_messages"] > 0
            else 0
        ),
    }
