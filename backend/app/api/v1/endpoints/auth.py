"""Authentication endpoints - local auth, token refresh, logout, and Google OAuth."""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import (
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.config import get_settings
from app.core.oauth import is_google_configured, oauth
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


# ============================================================
# LOCAL AUTHENTICATION
# ============================================================


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account with email and password."""
    auth_service = AuthService(db)
    user = await auth_service.register(
        email=request.email,
        username=request.username,
        password=request.password,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email/password and receive JWT tokens."""
    auth_service = AuthService(db)
    result = await auth_service.login(
        email=request.email,
        password=request.password,
    )
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    auth_service = AuthService(db)
    result = await auth_service.refresh_tokens(request.refresh_token)
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """Log out the current user.

    With stateless JWTs, logout is primarily handled client-side by deleting
    the stored tokens. This endpoint confirms the action and is the hook point
    for server-side token blacklisting if Redis is enabled later.
    """
    logger.info("User logged out", user_id=str(current_user.id))
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user's profile."""
    return current_user


# ============================================================
# GOOGLE OAUTH
# ============================================================


@router.get("/google/login")
async def google_login(request: Request):
    """Start the Google OAuth flow by redirecting to Google's consent screen."""
    if not is_google_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    google = oauth.create_client("google")
    # Authlib stores CSRF state in the session and validates it on callback
    return await google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google's OAuth callback, create/link the user, and redirect to frontend."""
    if not is_google_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    google = oauth.create_client("google")

    try:
        token = await google.authorize_access_token(request)
    except Exception as e:
        logger.warning("Google OAuth token exchange failed", error=str(e))
        return _redirect_with_error("google_auth_failed")

    # Extract user info (Authlib parses the OIDC id_token automatically)
    userinfo = token.get("userinfo")
    if not userinfo:
        try:
            resp = await google.get("https://openidconnect.googleapis.com/v1/userinfo", token=token)
            userinfo = resp.json()
        except Exception as e:
            logger.warning("Failed to fetch Google userinfo", error=str(e))
            return _redirect_with_error("google_userinfo_failed")

    auth_service = AuthService(db)
    try:
        result = await auth_service.authenticate_google(dict(userinfo))
    except Exception as e:
        logger.error("Google authentication failed", error=str(e))
        return _redirect_with_error("google_auth_failed")

    # Redirect to frontend with tokens in the URL fragment/query
    params = urlencode({
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"],
    })
    redirect_url = f"{settings.frontend_url}/auth/callback?{params}"
    return RedirectResponse(url=redirect_url)


def _redirect_with_error(error_code: str) -> RedirectResponse:
    """Redirect back to the frontend login page with an error code."""
    params = urlencode({"error": error_code})
    return RedirectResponse(url=f"{settings.frontend_url}/login?{params}")
