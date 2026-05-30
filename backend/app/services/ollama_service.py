"""Ollama Service - convenience wrapper around the provider factory.

Ollama runs local models and does not require an API key.
Base URL is configurable via OLLAMA_BASE_URL.
"""

from app.services.providers.factory import create_provider


def get_ollama_provider():
    """Get an Ollama (local) provider instance."""
    return create_provider("ollama")
