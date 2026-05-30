"""Together AI Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_together_provider():
    """Get a Together AI provider instance."""
    return create_provider("together")
