"""
Oximy SDK Utilities
"""

import secrets
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .constants import EVENT_ID_PREFIX

# URL-safe characters for nanoid
URL_SAFE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def nanoid(length: int) -> str:
    """Generates a random string of specified length using URL-safe characters."""
    return "".join(secrets.choice(URL_SAFE_CHARS) for _ in range(length))


def generate_event_id() -> str:
    """Generates a unique event ID. Format: evt_xxxxxxxxxxxxxxxxxxxxxx (21 random chars)"""
    return f"{EVENT_ID_PREFIX}{nanoid(21)}"


def get_timestamp() -> str:
    """Gets the current ISO8601 timestamp."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def get_nested_property(obj: Any, path: str) -> Any:
    """Safely extracts a nested property from an object."""
    if not isinstance(obj, dict):
        return None

    parts = path.split(".")
    current: Any = obj

    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)

    return current


def is_async_iterable(value: Any) -> bool:
    """Checks if a value is an async iterable (stream)."""
    return (
        value is not None
        and hasattr(value, "__aiter__")
        and callable(getattr(value, "__aiter__", None))
    )


def estimate_tokens(text: str) -> int:
    """Estimates token count from text (rough approximation). Uses ~4 characters per token."""
    return (len(text) + 3) // 4


def safe_stringify(obj: Any) -> str:
    """Safely stringifies an object, handling circular references."""
    import json

    seen = set()

    def _serialize(value: Any) -> Any:
        if isinstance(value, (dict, list)):
            if id(value) in seen:
                return "[Circular]"
            seen.add(id(value))
            if isinstance(value, dict):
                return {k: _serialize(v) for k, v in value.items()}
            else:
                return [_serialize(item) for item in value]
        return value

    try:
        return json.dumps(_serialize(obj))
    except (TypeError, ValueError):
        return str(obj)


def calculate_content_length(content: Any) -> int:
    """Calculates content length for various input types."""
    if isinstance(content, str):
        return len(content)

    if isinstance(content, list):
        total = 0
        for item in content:
            if isinstance(item, str):
                total += len(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    total += len(text)
        return total

    return 0


def create_debug_logger(enabled: bool):
    """Debug logger that only logs when debug mode is enabled."""

    def debug_logger(*args: Any) -> None:
        if enabled:
            print("[Oximy]", *args)

    return debug_logger


def extract_hostname(url: str) -> str | None:
    """Extracts hostname from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def deep_clone(obj: Any) -> Any:
    """Deep clones an object (simple implementation)."""
    import json

    if obj is None or not isinstance(obj, (dict, list)):
        return obj

    try:
        return json.loads(json.dumps(obj))
    except (TypeError, ValueError):
        # Fallback for non-serializable objects
        if isinstance(obj, dict):
            return {k: deep_clone(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [deep_clone(item) for item in obj]
        return obj


def truncate(text: str, max_length: int) -> str:
    """Truncates a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."