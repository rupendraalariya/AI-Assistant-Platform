"""Claude Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_claude_provider():
    """Get an Anthropic Claude provider instance."""
    return create_provider("claude")
