"""LLM Router - Dynamic provider selection, smart routing, and fallback.

This is the heart of the multi-provider system. It:
1. Instantiates the correct provider for a request
2. Supports automatic ("smart") model routing based on intent
3. Falls back to alternate providers when one fails
4. Never raises uncaught errors to the user
"""

import re
from typing import AsyncGenerator, Dict, List, Optional

from app.config import get_settings
from app.services.providers.base import BaseLLMProvider, ProviderResponse
from app.services.providers.claude_provider import ClaudeProvider
from app.services.providers.openai_compatible import OpenAICompatibleProvider
from app.services.providers.registry import (
    PROVIDER_REGISTRY,
    get_provider_config,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# Fallback chain - order matters. If a provider fails, try the next configured one.
FALLBACK_CHAIN = ["groq", "gemini", "deepseek", "openai", "mistral", "together"]


# Smart routing rules: detect intent from the prompt and pick the best provider/model.
# Each entry: (provider_id, model_id). If a provider isn't configured, the router
# automatically falls back to DEFAULT_PROVIDER.
SMART_ROUTES = {
    "coding": ("deepseek", "deepseek-chat"),
    "fast": ("groq", "llama-3.1-8b-instant"),
    "reasoning": ("groq", "llama-3.3-70b-versatile"),
    "research": ("gemini", "gemini-2.0-flash"),
    "simple": ("groq", "llama-3.1-8b-instant"),
}


class ProviderError(Exception):
    """Raised when a provider fails (used internally for fallback)."""


class LLMRouter:
    """Routes chat requests to the appropriate provider with fallback."""

    def _build_provider(self, provider_id: str) -> Optional[BaseLLMProvider]:
        """Instantiate a provider object for the given provider ID."""
        config = get_provider_config(provider_id)
        if not config:
            return None

        if config.client_type == "anthropic":
            return ClaudeProvider(config)
        return OpenAICompatibleProvider(config)

    def detect_intent(self, message: str) -> str:
        """Detect the intent of a message for smart routing."""
        msg = message.lower()

        # Coding indicators
        code_keywords = [
            "code", "function", "debug", "python", "javascript", "java ",
            "error", "bug", "compile", "algorithm", "```", "def ", "class ",
            "sql", "api", "refactor",
        ]
        if any(kw in msg for kw in code_keywords):
            return "coding"

        # Research / deep analysis indicators
        research_keywords = [
            "research", "analyze", "compare", "explain in detail",
            "comprehensive", "in-depth", "literature", "study", "essay",
        ]
        if any(kw in msg for kw in research_keywords):
            return "research"

        # Complex reasoning indicators
        reasoning_keywords = [
            "why", "prove", "solve", "calculate", "reason", "logic",
            "step by step", "math", "theorem",
        ]
        if any(kw in msg for kw in reasoning_keywords):
            return "reasoning"

        # Short/simple questions
        if len(message.split()) < 12:
            return "simple"

        return "fast"

    def resolve_provider_and_model(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> tuple:
        """Determine which provider and model to use.

        - If provider == "auto" or None, use smart routing.
        - Otherwise use the explicit provider, with its default or given model.
        """
        # Smart routing
        if not provider or provider == "auto":
            intent = self.detect_intent(message)
            routed_provider, routed_model = SMART_ROUTES.get(
                intent, (settings.default_provider, None)
            )
            config = get_provider_config(routed_provider)
            # If the smart-routed provider isn't configured, use default
            if not config or not config.is_configured:
                routed_provider = settings.default_provider
                config = get_provider_config(routed_provider)
                routed_model = None
            final_model = routed_model or (config.default_model if config else "")
            logger.info(
                "Smart routing applied",
                intent=intent,
                provider=routed_provider,
                model=final_model,
            )
            return routed_provider, final_model

        # Explicit provider
        config = get_provider_config(provider)
        if not config:
            raise ProviderError(f"Unknown provider: {provider}")
        final_model = model or config.default_model
        return provider, final_model

    def _build_fallback_order(self, primary_provider: str) -> List[str]:
        """Build the ordered list of providers to try, primary first."""
        order = [primary_provider]
        for p in FALLBACK_CHAIN:
            if p != primary_provider and p not in order:
                order.append(p)
        return order

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_fallback: bool = True,
    ) -> ProviderResponse:
        """Generate a chat response with automatic fallback.

        Tries the primary provider first. If it fails and fallback is enabled,
        cycles through the fallback chain until one succeeds.
        """
        primary, resolved_model = self.resolve_provider_and_model(
            messages[-1]["content"] if messages else "",
            provider,
            model,
        )

        providers_to_try = (
            self._build_fallback_order(primary) if enable_fallback else [primary]
        )

        last_error = None
        for prov_id in providers_to_try:
            config = get_provider_config(prov_id)
            if not config or not config.is_configured:
                continue

            # Use resolved model for primary, default model for fallbacks
            use_model = resolved_model if prov_id == primary else config.default_model
            if not config.get_model(use_model):
                use_model = config.default_model

            provider_obj = self._build_provider(prov_id)
            if not provider_obj:
                continue

            try:
                response = await provider_obj.generate(
                    messages=messages,
                    model=use_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if prov_id != primary:
                    logger.warning(
                        "Used fallback provider",
                        failed_provider=primary,
                        fallback_provider=prov_id,
                    )
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    "Provider failed, trying next in chain",
                    provider=prov_id,
                    error=str(e),
                )
                continue

        # All providers failed - return a graceful message instead of crashing
        logger.error("All providers failed", error=str(last_error))
        return ProviderResponse(
            content=(
                "I'm temporarily unable to reach any AI provider. "
                "Please check your API keys or try again shortly."
            ),
            provider="none",
            model="none",
        )

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_fallback: bool = True,
    ) -> AsyncGenerator[Dict, None]:
        """Stream a chat response with fallback.

        Yields dicts: {"content": str, "done": bool, "provider": str, "model": str}
        """
        primary, resolved_model = self.resolve_provider_and_model(
            messages[-1]["content"] if messages else "",
            provider,
            model,
        )

        providers_to_try = (
            self._build_fallback_order(primary) if enable_fallback else [primary]
        )

        for prov_id in providers_to_try:
            config = get_provider_config(prov_id)
            if not config or not config.is_configured:
                continue

            use_model = resolved_model if prov_id == primary else config.default_model
            if not config.get_model(use_model):
                use_model = config.default_model

            provider_obj = self._build_provider(prov_id)
            if not provider_obj:
                continue

            try:
                # Emit a metadata event so the frontend knows which provider answered
                yield {
                    "content": "",
                    "done": False,
                    "meta": True,
                    "provider": prov_id,
                    "model": use_model,
                }
                async for token in provider_obj.stream(
                    messages=messages,
                    model=use_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield {
                        "content": token,
                        "done": False,
                        "provider": prov_id,
                        "model": use_model,
                    }

                yield {
                    "content": "",
                    "done": True,
                    "provider": prov_id,
                    "model": use_model,
                }
                return
            except Exception as e:
                logger.warning(
                    "Stream provider failed, trying next",
                    provider=prov_id,
                    error=str(e),
                )
                continue

        # All failed
        yield {
            "content": "All AI providers are currently unavailable. Please try again.",
            "done": True,
            "provider": "none",
            "model": "none",
        }

    async def compare(
        self,
        messages: List[Dict[str, str]],
        providers: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> List[Dict]:
        """Send the same prompt to multiple providers and gather responses.

        Args:
            providers: list of {"provider": str, "model": str} dicts

        Returns:
            List of result dicts with provider, model, content, tokens, latency.
        """
        import asyncio

        async def _run_one(spec: Dict[str, str]) -> Dict:
            prov_id = spec.get("provider", "")
            model = spec.get("model", "")
            config = get_provider_config(prov_id)
            if not config or not config.is_configured:
                return {
                    "provider": prov_id,
                    "model": model,
                    "content": f"Provider '{prov_id}' is not configured.",
                    "error": True,
                    "total_tokens": 0,
                    "latency_ms": 0,
                    "cost": 0.0,
                }
            if not model:
                model = config.default_model

            provider_obj = self._build_provider(prov_id)
            try:
                resp = await provider_obj.generate(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return {
                    "provider": resp.provider,
                    "model": resp.model,
                    "content": resp.content,
                    "error": False,
                    "total_tokens": resp.total_tokens,
                    "latency_ms": resp.latency_ms,
                    "cost": resp.cost,
                }
            except Exception as e:
                return {
                    "provider": prov_id,
                    "model": model,
                    "content": f"Error: {str(e)}",
                    "error": True,
                    "total_tokens": 0,
                    "latency_ms": 0,
                    "cost": 0.0,
                }

        # Run all providers concurrently
        tasks = [_run_one(spec) for spec in providers]
        return await asyncio.gather(*tasks)


# Singleton router instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get or create the LLM router singleton."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
