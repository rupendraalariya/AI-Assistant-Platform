"""Base LLM Provider - Abstract interface all providers implement."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional

from app.services.providers.registry import ProviderConfig


@dataclass
class ProviderResponse:
    """Standardized response from any LLM provider."""

    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    cost: float = 0.0


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers.

    Defines the contract every provider must fulfill:
    - generate(): non-streaming completion
    - stream(): streaming token generation
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.provider_id = config.id

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        """Generate a complete (non-streaming) response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens as they are generated."""
        ...

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculate cost based on model pricing."""
        model_info = self.config.get_model(model)
        if not model_info:
            return 0.0
        input_cost = (prompt_tokens / 1000) * model_info.input_cost
        output_cost = (completion_tokens / 1000) * model_info.output_cost
        return round(input_cost + output_cost, 6)
