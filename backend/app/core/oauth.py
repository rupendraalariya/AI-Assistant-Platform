"""OAuth client configuration using Authlib.

Registers the Google OAuth provider and exposes the configured client.
Google's OpenID Connect discovery document is used so we never hardcode
authorization/token endpoints.
"""

from authlib.integrations.starlette_client import OAuth

from app.config import get_settings

settings = get_settings()

oauth = OAuth()

# Register Google only if credentials are present
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )


def is_google_configured() -> bool:
    """Check whether Google OAuth credentials are configured."""
    return bool(settings.google_client_id and settings.google_client_secret)
