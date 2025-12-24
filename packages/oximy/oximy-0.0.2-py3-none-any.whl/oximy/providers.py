"""
Provider Detection

Automatically detects the LLM provider from client configuration.
"""

import re
from typing import Any

from .constants import (
    AZURE_OPENAI_PATTERN,
    BEDROCK_PATTERN,
    OLLAMA_PATTERN,
    PROVIDER_BASE_URLS,
)
from .types import Provider
from .utils import extract_hostname


def extract_base_url(client: Any) -> str | None:
    """Extracts the base URL from a client object."""
    if client is None:
        return None

    # Handle dict clients (from tests)
    if isinstance(client, dict):
        # Check _client.baseURL structure
        if "_client" in client:
            inner_client = client["_client"]
            if isinstance(inner_client, dict):
                base_url = inner_client.get("baseURL") or inner_client.get("base_url") or inner_client.get("baseUrl")
                if isinstance(base_url, str):
                    return base_url
            elif hasattr(inner_client, "baseURL"):
                base_url = getattr(inner_client, "baseURL")
                if isinstance(base_url, str):
                    return base_url
        
        # Check direct properties
        base_url = client.get("baseURL") or client.get("base_url") or client.get("baseUrl")
        if isinstance(base_url, str):
            return base_url
        
        # Check _baseURL (Anthropic)
        base_url = client.get("_baseURL") or client.get("_base_url")
        if isinstance(base_url, str):
            return base_url
        
        return None

    if not isinstance(client, object):
        return None

    # OpenAI SDK v4+ stores it in _client.baseURL (camelCase)
    if hasattr(client, "_client"):
        inner_client = getattr(client, "_client")
        if inner_client and isinstance(inner_client, dict):
            base_url = inner_client.get("baseURL") or inner_client.get("base_url")
            if isinstance(base_url, str):
                return base_url
        elif hasattr(inner_client, "baseURL"):
            base_url = getattr(inner_client, "baseURL")
            if isinstance(base_url, str):
                return base_url
        elif hasattr(inner_client, "base_url"):
            base_url = getattr(inner_client, "base_url")
            if isinstance(base_url, str):
                return base_url

    # Direct properties (check both camelCase and snake_case)
    if isinstance(client, dict):
        base_url = client.get("baseURL") or client.get("base_url") or client.get("baseUrl")
        if isinstance(base_url, str):
            return base_url
    else:
        if hasattr(client, "baseURL"):
            base_url = getattr(client, "baseURL")
            if isinstance(base_url, str):
                return base_url
        if hasattr(client, "base_url"):
            base_url = getattr(client, "base_url")
            if isinstance(base_url, str):
                return base_url
        if hasattr(client, "baseUrl"):
            base_url = getattr(client, "baseUrl")
            if isinstance(base_url, str):
                return base_url

    # Anthropic SDK
    if isinstance(client, dict):
        base_url = client.get("_baseURL") or client.get("_base_url")
        if isinstance(base_url, str):
            return base_url
    elif hasattr(client, "_baseURL"):
        base_url = getattr(client, "_baseURL")
        if isinstance(base_url, str):
            return base_url
    elif hasattr(client, "_base_url"):
        base_url = getattr(client, "_base_url")
        if isinstance(base_url, str):
            return base_url

    # Google Generative AI
    if hasattr(client, "_api_endpoint"):
        endpoint = getattr(client, "_api_endpoint")
        if isinstance(endpoint, str):
            return endpoint

    return None


def detect_provider_from_url(base_url: str) -> Provider:
    """Detects the provider from a base URL."""
    hostname = extract_hostname(base_url)
    if not hostname:
        return "custom"

    # Check exact matches (hostname includes pattern)
    for pattern, provider in PROVIDER_BASE_URLS.items():
        if pattern in hostname:
            return provider  # type: ignore

    # Check patterns against full URL (not just hostname)
    if re.search(AZURE_OPENAI_PATTERN, base_url):
        return "azure"

    if re.search(BEDROCK_PATTERN, base_url):
        return "bedrock"

    if re.search(OLLAMA_PATTERN, base_url):
        return "ollama"

    return "custom"


def detect_provider(client: Any) -> Provider:
    """Detects the provider from a client object."""
    base_url = extract_base_url(client)
    if base_url:
        return detect_provider_from_url(base_url)

    # Default to OpenAI if no baseURL (common case) - matches TypeScript behavior
    return "openai"


def detect_event_type(method_path: str) -> str:
    """Detects event type from method path."""
    path_lower = method_path.lower()

    if "chat.completions" in path_lower or "messages" in path_lower:
        return "completion"

    if "completions" in path_lower and "chat" not in path_lower:
        return "completion"

    if "responses" in path_lower:
        return "completion"

    if "embedding" in path_lower:
        return "embedding"
    if "image" in path_lower:
        return "image"
    if "audio" in path_lower or "speech" in path_lower or "transcription" in path_lower:
        return "audio"
    if "moderation" in path_lower:
        return "moderation"
    if "file" in path_lower:
        return "file"
    if "assistant" in path_lower:
        return "assistant"
    if "thread" in path_lower:
        return "thread"

    return "other"


def get_api_type(method_path: str) -> str:
    """Extracts API type from method path."""
    # Remove common prefixes
    path = method_path.replace("create", "").replace("stream", "").strip(".")
    return path or "unknown"
