"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import analytics, auth, chat, documents, health, providers, sessions

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(providers.router, tags=["Multi-Provider"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
