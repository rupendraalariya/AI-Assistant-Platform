"""Unit tests for the LLM Router - smart routing and fallback logic."""

import pytest

from app.services.llm_router import LLMRouter, FALLBACK_CHAIN
from app.services.providers.registry import (
    PROVIDER_REGISTRY,
    get_provider_config,
    list_providers,
    list_models,
)


class TestProviderRegistry:
    """Tests for the provider registry."""

    def test_all_providers_present(self):
        expected = {
            "openai", "gemini", "claude", "groq",
            "deepseek", "mistral", "together", "ollama",
        }
        assert expected.issubset(set(PROVIDER_REGISTRY.keys()))

    def test_get_provider_config(self):
        config = get_provider_config("openai")
        assert config is not None
        assert config.id == "openai"
        assert len(config.models) > 0

    def test_get_unknown_provider(self):
        assert get_provider_config("nonexistent") is None

    def test_case_insensitive_lookup(self):
        assert get_provider_config("OpenAI") is not None
        assert get_provider_config("OPENAI") is not None

    def test_list_providers(self):
        providers = list_providers()
        assert len(providers) == 8
        for p in providers:
            assert "id" in p
            assert "name" in p
            assert "configured" in p

    def test_list_models(self):
        models = list_models("openai")
        assert len(models) > 0
        assert all("id" in m for m in models)

    def test_ollama_does_not_require_key(self):
        config = get_provider_config("ollama")
        assert config.requires_key is False
        assert config.is_configured is True  # always configured

    def test_default_model(self):
        config = get_provider_config("groq")
        assert config.default_model == config.models[0].id


class TestSmartRouting:
    """Tests for intent detection and smart routing."""

    def setup_method(self):
        self.router = LLMRouter()

    def test_detect_coding_intent(self):
        assert self.router.detect_intent("Write a Python function to reverse a string") == "coding"
        assert self.router.detect_intent("Help me debug this error in my code") == "coding"

    def test_detect_research_intent(self):
        assert self.router.detect_intent("Research and analyze the history of AI in detail") == "research"

    def test_detect_reasoning_intent(self):
        assert self.router.detect_intent("Why is the sky blue? Prove it step by step") == "reasoning"

    def test_detect_simple_intent(self):
        assert self.router.detect_intent("What is 2+2?") == "simple"

    def test_detect_fast_default(self):
        # A medium-length non-special message
        result = self.router.detect_intent(
            "Tell me about the weather patterns in tropical regions during summer months generally"
        )
        assert result in ("fast", "research", "reasoning")


class TestFallbackChain:
    """Tests for the fallback ordering logic."""

    def setup_method(self):
        self.router = LLMRouter()

    def test_fallback_order_primary_first(self):
        order = self.router._build_fallback_order("openai")
        assert order[0] == "openai"

    def test_fallback_includes_chain(self):
        order = self.router._build_fallback_order("groq")
        assert order[0] == "groq"
        # All fallback providers should appear
        for p in FALLBACK_CHAIN:
            assert p in order

    def test_no_duplicates_in_fallback(self):
        order = self.router._build_fallback_order("gemini")
        assert len(order) == len(set(order))


class TestProviderResolution:
    """Tests for resolving provider and model from a request."""

    def setup_method(self):
        self.router = LLMRouter()

    def test_explicit_provider(self):
        provider, model = self.router.resolve_provider_and_model(
            "hello", provider="openai", model="gpt-4o"
        )
        assert provider == "openai"
        assert model == "gpt-4o"

    def test_explicit_provider_default_model(self):
        provider, model = self.router.resolve_provider_and_model(
            "hello", provider="groq", model=None
        )
        assert provider == "groq"
        assert model != ""  # uses default

    def test_auto_routing(self):
        provider, model = self.router.resolve_provider_and_model(
            "Write a function", provider="auto", model=None
        )
        # Should resolve to some configured provider
        assert provider in PROVIDER_REGISTRY
        assert model != ""
