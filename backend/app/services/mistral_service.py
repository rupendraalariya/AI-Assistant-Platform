"""Mistral Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_mistral_provider():
    """Get a Mistral AI provider instance."""
    return create_provider("mistral")
