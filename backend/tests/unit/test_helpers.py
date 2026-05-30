"""Unit tests for helper utilities."""

import pytest

from app.utils.helpers import (
    format_session_title,
    generate_uuid,
    sanitize_filename,
    truncate_text,
)


class TestGenerateUUID:
    def test_returns_string(self):
        result = generate_uuid()
        assert isinstance(result, str)

    def test_unique_values(self):
        ids = {generate_uuid() for _ in range(100)}
        assert len(ids) == 100


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("hello", 100) == "hello"

    def test_long_text_truncated(self):
        text = "a" * 200
        result = truncate_text(text, 100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_exact_length(self):
        text = "a" * 100
        assert truncate_text(text, 100) == text


class TestSanitizeFilename:
    def test_normal_filename(self):
        assert sanitize_filename("document.pdf") == "document.pdf"

    def test_path_traversal(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_special_characters(self):
        result = sanitize_filename("file name (1).pdf")
        assert " " not in result
        assert "(" not in result

    def test_empty_filename(self):
        result = sanitize_filename("")
        assert result == "unnamed_file"


class TestFormatSessionTitle:
    def test_short_message(self):
        assert format_session_title("Hello") == "Hello"

    def test_long_message_truncated(self):
        long_msg = "This is a very long message that should be truncated for the session title"
        result = format_session_title(long_msg)
        assert len(result) <= 50
