"""Claude Provider - Anthropic native SDK implementation.

Claude uses a different message format than OpenAI:
- System prompt is a separate top-level parameter, not a message.
- Uses the Anthropic Messages API.
"""

import time
from typing import AsyncGenerator, Dict, List, Tuple

from app.services.providers.base import BaseLLMProvider, ProviderResponse
from app.services.providers.registry import ProviderConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """Lazily create the Anthropic async client."""
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=60.0,
                max_retries=2,
            )
        return self._client

    def _split_system(self, messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
        """Separate the system prompt from conversation messages."""
        system_prompt = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})
        # Anthropic requires the first message to be from "user"
        if chat_messages and chat_messages[0]["role"] != "user":
            chat_messages.insert(0, {"role": "user", "content": "Continue."})
        return system_prompt.strip(), chat_messages

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
        system_prompt, chat_messages = self._split_system(messages)

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await client.messages.create(**kwargs)

        latency_ms = int((time.time() - start_time) * 1000)

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        logger.info(
            "Claude response generated",
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
        system_prompt, chat_messages = self._split_system(messages)

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
