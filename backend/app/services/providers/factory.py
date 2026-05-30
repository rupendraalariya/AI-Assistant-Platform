"""Provider Factory - Creates provider instances by ID.

Centralizes provider instantiation so the router and individual
service modules share one construction path.
"""

from typing import Optional

from app.services.providers.base import BaseLLMProvider
from app.services.providers.claude_provider import ClaudeProvider
from app.services.providers.openai_compatible import OpenAICompatibleProvider
from app.services.providers.registry import get_provider_config


def create_provider(provider_id: str) -> Optional[BaseLLMProvider]:
    """Create a provider instance for the given provider ID.

    Returns None if the provider is unknown.
    """
    config = get_provider_config(provider_id)
    if not config:
        return None

    if config.client_type == "anthropic":
        return ClaudeProvider(config)
    return OpenAICompatibleProvider(config)
