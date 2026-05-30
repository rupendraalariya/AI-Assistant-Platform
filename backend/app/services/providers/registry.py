"""Provider Registry - Central catalog of all LLM providers and models.

Most providers expose OpenAI-compatible APIs, so we use a unified client
with different base URLs. This is the same approach used by OpenRouter.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.config import get_settings

settings = get_settings()


@dataclass
class ModelInfo:
    """Information about a specific model."""

    id: str
    name: str
    context_window: int = 8192
    # Cost per 1K tokens (USD)
    input_cost: float = 0.0
    output_cost: float = 0.0
    supports_streaming: bool = True


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    id: str
    name: str
    base_url: Optional[str]  # None for native SDK providers
    api_key_setting: str  # name of the settings attribute holding the key
    models: List[ModelInfo] = field(default_factory=list)
    # "openai_compatible" providers use the OpenAI SDK with base_url
    client_type: str = "openai_compatible"
    requires_key: bool = True

    @property
    def api_key(self) -> str:
        """Get the API key for this provider from settings."""
        return getattr(settings, self.api_key_setting, "") or ""

    @property
    def is_configured(self) -> bool:
        """Check if the provider has a valid API key (or doesn't need one)."""
        if not self.requires_key:
            return True
        return bool(self.api_key)

    @property
    def default_model(self) -> str:
        """Get the default (first) model for this provider."""
        return self.models[0].id if self.models else ""

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Find a model by ID."""
        for model in self.models:
            if model.id == model_id:
                return model
        return None


# ============================================================
# PROVIDER REGISTRY
# ============================================================

PROVIDER_REGISTRY: Dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        id="openai",
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_setting="openai_api_key",
        models=[
            ModelInfo("gpt-4o-mini", "GPT-4o Mini", 128000, 0.00015, 0.0006),
            ModelInfo("gpt-4o", "GPT-4o", 128000, 0.005, 0.015),
            ModelInfo("gpt-4-turbo", "GPT-4 Turbo", 128000, 0.01, 0.03),
            ModelInfo("gpt-3.5-turbo", "GPT-3.5 Turbo", 16385, 0.0005, 0.0015),
        ],
    ),
    "gemini": ProviderConfig(
        id="gemini",
        name="Google Gemini",
        # Gemini exposes an OpenAI-compatible endpoint
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_setting="gemini_api_key",
        models=[
            ModelInfo("gemini-2.0-flash", "Gemini 2.0 Flash", 1000000, 0.0, 0.0),
            ModelInfo("gemini-1.5-flash", "Gemini 1.5 Flash", 1000000, 0.000075, 0.0003),
            ModelInfo("gemini-1.5-pro", "Gemini 1.5 Pro", 2000000, 0.00125, 0.005),
        ],
    ),
    "claude": ProviderConfig(
        id="claude",
        name="Anthropic Claude",
        base_url=None,  # Uses native Anthropic SDK
        api_key_setting="anthropic_api_key",
        client_type="anthropic",
        models=[
            ModelInfo("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet", 200000, 0.003, 0.015),
            ModelInfo("claude-3-5-haiku-20241022", "Claude 3.5 Haiku", 200000, 0.0008, 0.004),
            ModelInfo("claude-3-opus-20240229", "Claude 3 Opus", 200000, 0.015, 0.075),
        ],
    ),
    "groq": ProviderConfig(
        id="groq",
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_setting="groq_api_key",
        models=[
            ModelInfo("llama-3.3-70b-versatile", "Llama 3.3 70B", 128000, 0.00059, 0.00079),
            ModelInfo("llama-3.1-8b-instant", "Llama 3.1 8B", 128000, 0.00005, 0.00008),
            ModelInfo("qwen-2.5-32b", "Qwen 2.5 32B", 128000, 0.00029, 0.00039),
            ModelInfo("mixtral-8x7b-32768", "Mixtral 8x7B", 32768, 0.00024, 0.00024),
        ],
    ),
    "deepseek": ProviderConfig(
        id="deepseek",
        name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        api_key_setting="deepseek_api_key",
        models=[
            ModelInfo("deepseek-chat", "DeepSeek Chat", 64000, 0.00027, 0.0011),
            ModelInfo("deepseek-reasoner", "DeepSeek Reasoner", 64000, 0.00055, 0.00219),
        ],
    ),
    "mistral": ProviderConfig(
        id="mistral",
        name="Mistral AI",
        base_url="https://api.mistral.ai/v1",
        api_key_setting="mistral_api_key",
        models=[
            ModelInfo("mistral-large-latest", "Mistral Large", 128000, 0.002, 0.006),
            ModelInfo("mistral-small-latest", "Mistral Small", 128000, 0.0002, 0.0006),
            ModelInfo("open-mistral-nemo", "Mistral Nemo", 128000, 0.00015, 0.00015),
        ],
    ),
    "together": ProviderConfig(
        id="together",
        name="Together AI",
        base_url="https://api.together.xyz/v1",
        api_key_setting="together_api_key",
        models=[
            ModelInfo("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Llama 3.3 70B Turbo", 128000, 0.00088, 0.00088),
            ModelInfo("mistralai/Mixtral-8x7B-Instruct-v0.1", "Mixtral 8x7B", 32768, 0.0006, 0.0006),
            ModelInfo("Qwen/Qwen2.5-72B-Instruct-Turbo", "Qwen 2.5 72B", 32768, 0.0012, 0.0012),
        ],
    ),
    "ollama": ProviderConfig(
        id="ollama",
        name="Ollama (Local)",
        base_url=f"{settings.ollama_base_url}/v1",
        api_key_setting="ollama_base_url",  # not really a key
        requires_key=False,
        models=[
            ModelInfo("llama3.2", "Llama 3.2", 128000, 0.0, 0.0),
            ModelInfo("qwen2.5", "Qwen 2.5", 32768, 0.0, 0.0),
            ModelInfo("deepseek-coder-v2", "DeepSeek Coder V2", 16384, 0.0, 0.0),
            ModelInfo("mistral", "Mistral", 32768, 0.0, 0.0),
        ],
    ),
}


def get_provider_config(provider_id: str) -> Optional[ProviderConfig]:
    """Get configuration for a provider by ID."""
    return PROVIDER_REGISTRY.get(provider_id.lower())


def list_providers(only_configured: bool = False) -> List[Dict]:
    """List all providers with their metadata."""
    result = []
    for config in PROVIDER_REGISTRY.values():
        if only_configured and not config.is_configured:
            continue
        result.append({
            "id": config.id,
            "name": config.name,
            "configured": config.is_configured,
            "requires_key": config.requires_key,
            "model_count": len(config.models),
        })
    return result


def list_models(provider_id: str) -> List[Dict]:
    """List all models for a given provider."""
    config = get_provider_config(provider_id)
    if not config:
        return []
    return [
        {
            "id": m.id,
            "name": m.name,
            "context_window": m.context_window,
            "input_cost": m.input_cost,
            "output_cost": m.output_cost,
            "supports_streaming": m.supports_streaming,
        }
        for m in config.models
    ]
