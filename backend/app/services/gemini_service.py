"""Gemini Service - convenience wrapper around the provider factory."""

from app.services.providers.factory import create_provider


def get_gemini_provider():
    """Get a Google Gemini provider instance."""
    return create_provider("gemini")
