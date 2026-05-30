"""General utility helpers."""

import uuid
from datetime import datetime, timezone
from typing import Optional


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal."""
    import os
    basename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dots, hyphens, underscores
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
    sanitized = "".join(c if c in safe_chars else "_" for c in basename)
    return sanitized or "unnamed_file"


def format_session_title(first_message: str) -> str:
    """Generate a session title from the first user message."""
    return truncate_text(first_message, max_length=50)
