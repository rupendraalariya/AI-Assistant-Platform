"""DeepSeek Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_deepseek_provider():
    """Get a DeepSeek provider instance."""
    return create_provider("deepseek")
