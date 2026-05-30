"""OpenAI Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_openai_provider():
    """Get an OpenAI provider instance."""
    return create_provider("openai")
