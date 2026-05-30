"""Groq Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_groq_provider():
    """Get a Groq provider instance."""
    return create_provider("groq")
