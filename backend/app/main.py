"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.middleware import LoggingMiddleware, ExceptionHandlerMiddleware
from app.db.database import init_db, close_db
from app.db.redis import init_redis, close_redis, is_redis_available
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan - startup and shutdown.

    Startup never fails. External services (Redis) are optional.
    """
    logger.info("Starting application", app_name=settings.app_name)

    # Database is required
    await init_db()

    # Redis is optional - init_redis never raises
    await init_redis()

    if is_redis_available():
        logger.info("Memory backend: Redis")
    else:
        logger.info("Memory backend: In-memory (Redis unavailable)")

    logger.info(
        "Application ready",
        docs_url=f"http://localhost:{settings.api_port}/docs",
    )

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_redis()
    await close_db()


def create_application() -> FastAPI:
    """Application factory pattern."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-Grade LLM Chatbot with RAG, Memory, and Streaming",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware stack
    application.add_middleware(ExceptionHandlerMiddleware)
    application.add_middleware(LoggingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # SessionMiddleware is required by Authlib to store OAuth state (CSRF protection)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        same_site="lax",
        https_only=settings.environment == "production",
    )

    # Routes
    application.include_router(api_router, prefix=settings.api_prefix)

    return application


app = create_application()
