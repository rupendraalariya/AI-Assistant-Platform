"""Unit tests for cost optimization service."""

import pytest

from app.services.cost_service import CostService


class TestCostService:
    """Tests for CostService."""

    def setup_method(self):
        self.service = CostService()

    def test_compress_context_short(self):
        """Short context should not be compressed."""
        context = "This is a short context."
        result = self.service.compress_context(context, max_tokens=100)
        assert result == context

    def test_compress_context_long(self):
        """Long context should be trimmed."""
        context = ". ".join(["This is sentence number " + str(i) for i in range(100)])
        result = self.service.compress_context(context, max_tokens=50)
        assert len(result) < len(context)

    def test_trim_chat_history_short(self):
        """Short history should not be trimmed."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        result = self.service.trim_chat_history(messages, max_tokens=1000)
        assert len(result) == 2

    def test_trim_chat_history_long(self):
        """Long history should be trimmed from the beginning."""
        messages = [
            {"role": "user", "content": f"Message {i} " * 50}
            for i in range(20)
        ]
        result = self.service.trim_chat_history(messages, max_tokens=500)
        assert len(result) < len(messages)
        # Should keep most recent messages
        assert result[-1] == messages[-1]

    def test_calculate_session_cost(self):
        """Should calculate cost correctly."""
        result = self.service.calculate_session_cost(1000, 500, "gpt-4o-mini")
        assert "prompt_tokens" in result
        assert "completion_tokens" in result
        assert "total_tokens" in result
        assert "cost_usd" in result
        assert result["total_tokens"] == 1500
        assert result["cost_usd"] > 0

    def test_optimization_suggestions_high_tokens(self):
        """Should suggest compression for high token usage."""
        suggestions = self.service.get_optimization_suggestions(
            total_tokens=150000,
            avg_tokens_per_message=600,
            session_count=10,
        )
        assert len(suggestions) > 0
