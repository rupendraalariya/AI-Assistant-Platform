"""Authentication Service - User management, JWT, and OAuth operations."""

import re
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- Helpers ----------

    def _issue_tokens(self, user: User) -> dict:
        """Generate access + refresh tokens for a user."""
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user": user,
        }

    async def _unique_username(self, base: str) -> str:
        """Generate a unique username from a base string."""
        # Sanitize
        candidate = re.sub(r"[^a-zA-Z0-9_]", "", base) or "user"
        candidate = candidate[:90]

        # Check uniqueness, append suffix if needed
        suffix = 0
        final = candidate
        while True:
            existing = await self.db.execute(
                select(User).where(User.username == final)
            )
            if not existing.scalar_one_or_none():
                return final
            suffix += 1
            final = f"{candidate}{suffix}"

    # ---------- Local auth ----------

    async def register(self, email: str, username: str, password: str) -> User:
        """Register a new local user."""
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValidationError("Email already registered")

        existing = await self.db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            raise ValidationError("Username already taken")

        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            auth_provider="local",
        )
        self.db.add(user)
        await self.db.flush()

        logger.info("User registered", user_id=str(user.id), username=username)
        return user

    async def login(self, email: str, password: str) -> dict:
        """Authenticate a local user and return tokens."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        # Reject if no user, or user has no password (Google-only account)
        if not user or not user.hashed_password:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        logger.info("User logged in", user_id=str(user.id))
        return self._issue_tokens(user)

    # ---------- Token refresh ----------

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """Issue new tokens from a valid refresh token (token rotation)."""
        payload = decode_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        try:
            user = await self.get_user_by_id(user_id)
        except NotFoundError:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        logger.info("Tokens refreshed", user_id=str(user.id))
        return self._issue_tokens(user)

    # ---------- Google OAuth ----------

    async def authenticate_google(self, userinfo: dict) -> dict:
        """Find or create a user from Google userinfo, then issue tokens.

        Flow:
        1. If a user exists with this google_id -> log them in.
        2. Else if a user exists with this email -> link Google to that account.
        3. Else -> create a brand new Google account.

        Args:
            userinfo: dict from Google with keys: sub, email, name, picture, ...
        """
        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name") or (email.split("@")[0] if email else "user")
        picture = userinfo.get("picture")

        if not google_id or not email:
            raise AuthenticationError("Google did not return required profile info")

        # 1. Existing Google user
        result = await self.db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if user:
            # Refresh profile picture if changed
            if picture and user.profile_picture != picture:
                user.profile_picture = picture
            await self.db.flush()
            logger.info("Google login (existing)", user_id=str(user.id))
            return self._issue_tokens(user)

        # 2. Existing email account -> link Google
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.google_id = google_id
            user.profile_picture = picture or user.profile_picture
            # Keep auth_provider; if it was local, mark it as supporting google too.
            if user.auth_provider == "local":
                user.auth_provider = "google"
            await self.db.flush()
            logger.info("Google account linked", user_id=str(user.id))
            return self._issue_tokens(user)

        # 3. Create new Google user
        username = await self._unique_username(name)
        user = User(
            email=email,
            username=username,
            hashed_password=None,  # no password for Google-only accounts
            google_id=google_id,
            auth_provider="google",
            profile_picture=picture,
        )
        self.db.add(user)
        await self.db.flush()
        logger.info("Google account created", user_id=str(user.id))
        return self._issue_tokens(user)

    # ---------- Lookups ----------

    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT access token."""
        payload = decode_token(token)
        if not payload:
            raise AuthenticationError("Invalid or expired token")

        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        try:
            return await self.get_user_by_id(user_id)
        except NotFoundError:
            raise AuthenticationError("User not found")
