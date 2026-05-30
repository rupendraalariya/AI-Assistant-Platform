"""OpenAI-Compatible Provider - Works with any OpenAI-compatible API.

Handles: OpenAI, Gemini, Groq, DeepSeek, Mistral, Together AI, Ollama.
All these providers expose the same /chat/completions endpoint format,
so a single implementation with different base URLs covers all of them.
"""

import time
from typing import AsyncGenerator, Dict, List

from app.services.providers.base import BaseLLMProvider, ProviderResponse
from app.services.providers.registry import ProviderConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for any OpenAI-compatible API endpoint."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None
        self._async_client = None

    def _get_client(self):
        """Lazily create the async OpenAI client pointed at this provider."""
        if self._async_client is None:
            from openai import AsyncOpenAI

            # Ollama doesn't need a real key
            api_key = self.config.api_key or "not-needed"
            self._async_client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.base_url,
                timeout=60.0,
                max_retries=2,
            )
        return self._async_client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> ProviderResponse:
        """Generate a complete response."""
        start_time = time.time()
        client = self._get_client()

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        content = response.choices[0].message.content or ""
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        logger.info(
            "Provider response generated",
            provider=self.provider_id,
            model=model,
            tokens=total_tokens,
            latency_ms=latency_ms,
        )

        return ProviderResponse(
            content=content,
            provider=self.provider_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost=cost,
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        client = self._get_client()

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
