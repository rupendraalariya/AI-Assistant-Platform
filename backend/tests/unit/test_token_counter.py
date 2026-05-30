"""Unit tests for token counter utilities."""

import pytest

from app.utils.token_counter import count_tokens, count_messages_tokens, estimate_cost


class TestCountTokens:
    """Tests for count_tokens function."""

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        tokens = count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10

    def test_longer_text(self):
        text = "This is a longer piece of text that should have more tokens."
        tokens = count_tokens(text)
        assert tokens > 5

    def test_different_models(self):
        text = "Test text for token counting"
        tokens_mini = count_tokens(text, "gpt-4o-mini")
        tokens_gpt4 = count_tokens(text, "gpt-4")
        # Both should return positive values
        assert tokens_mini > 0
        assert tokens_gpt4 > 0


class TestCountMessagesTokens:
    """Tests for count_messages_tokens function."""

    def test_single_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        tokens = count_messages_tokens(messages)
        assert tokens > 0

    def test_multiple_messages(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = count_messages_tokens(messages)
        assert tokens > count_messages_tokens([messages[0]])

    def test_empty_messages(self):
        tokens = count_messages_tokens([])
        assert tokens == 3  # Base tokens for reply priming


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_zero_tokens(self):
        cost = estimate_cost(0, 0)
        assert cost == 0.0

    def test_gpt4o_mini_cost(self):
        cost = estimate_cost(1000, 1000, "gpt-4o-mini")
        assert cost > 0
        assert cost < 0.01  # Should be very cheap

    def test_gpt4_cost(self):
        cost = estimate_cost(1000, 1000, "gpt-4")
        assert cost > 0
        # GPT-4 should be more expensive than mini
        mini_cost = estimate_cost(1000, 1000, "gpt-4o-mini")
        assert cost > mini_cost

    def test_unknown_model_uses_default(self):
        cost = estimate_cost(1000, 1000, "unknown-model")
        default_cost = estimate_cost(1000, 1000, "gpt-4o-mini")
        assert cost == default_cost
