"""Tests for providers module - exact match of providers.test.ts"""

import pytest

from oximy.providers import (
    detect_event_type,
    detect_provider,
    detect_provider_from_url,
    extract_base_url,
    get_api_type,
)


class TestExtractBaseUrl:
    """Tests for extractBaseUrl - exact match of TypeScript tests."""

    def test_should_extract_baseurl_from_openai_sdk_v4_structure(self):
        """should extract baseURL from OpenAI SDK v4+ structure"""
        client = {
            "_client": {
                "baseURL": "https://api.openai.com/v1",
            },
        }

        assert extract_base_url(client) == "https://api.openai.com/v1"

    def test_should_extract_direct_baseurl_property(self):
        """should extract direct baseURL property"""
        client = {
            "baseURL": "https://api.anthropic.com/v1",
        }

        assert extract_base_url(client) == "https://api.anthropic.com/v1"

    def test_should_return_none_for_client_without_baseurl(self):
        """should return undefined for client without baseURL"""
        client = {"someOtherProp": True}

        assert extract_base_url(client) is None


class TestDetectProviderFromUrl:
    """Tests for detectProviderFromUrl - exact match of TypeScript tests."""

    def test_should_detect_openai(self):
        """should detect OpenAI"""
        assert detect_provider_from_url("https://api.openai.com/v1") == "openai"

    def test_should_detect_anthropic(self):
        """should detect Anthropic"""
        assert detect_provider_from_url("https://api.anthropic.com/v1") == "anthropic"

    def test_should_detect_openrouter(self):
        """should detect OpenRouter"""
        assert detect_provider_from_url("https://openrouter.ai/api/v1") == "openrouter"

    def test_should_detect_groq(self):
        """should detect Groq"""
        assert detect_provider_from_url("https://api.groq.com/v1") == "groq"

    def test_should_detect_azure_openai(self):
        """should detect Azure OpenAI"""
        assert detect_provider_from_url("https://myresource.openai.azure.com/v1") == "azure"

    def test_should_detect_aws_bedrock(self):
        """should detect AWS Bedrock"""
        assert (
            detect_provider_from_url("https://bedrock-runtime.us-east-1.amazonaws.com") == "bedrock"
        )

    def test_should_detect_ollama(self):
        """should detect Ollama"""
        assert detect_provider_from_url("http://localhost:11434") == "ollama"

    def test_should_return_custom_for_unknown_urls(self):
        """should return custom for unknown URLs"""
        assert detect_provider_from_url("https://my-custom-api.com/v1") == "custom"


class TestDetectProvider:
    """Tests for detectProvider - exact match of TypeScript tests."""

    def test_should_detect_provider_from_client_baseurl(self):
        """should detect provider from client baseURL"""
        client = {
            "_client": {
                "baseURL": "https://api.anthropic.com/v1",
            },
        }

        assert detect_provider(client) == "anthropic"

    def test_should_default_to_openai_when_no_baseurl(self):
        """should default to openai when no baseURL"""
        client = {}

        assert detect_provider(client) == "openai"


class TestDetectEventType:
    """Tests for detectEventType - exact match of TypeScript tests."""

    def test_should_detect_completion_from_chat_completions(self):
        """should detect completion from chat.completions"""
        assert detect_event_type("chat.completions.create") == "completion"

    def test_should_detect_completion_from_messages(self):
        """should detect completion from messages"""
        assert detect_event_type("messages.create") == "completion"

    def test_should_detect_completion_from_responses(self):
        """should detect completion from responses"""
        assert detect_event_type("responses.create") == "completion"

    def test_should_detect_embedding(self):
        """should detect embedding"""
        assert detect_event_type("embeddings.create") == "embedding"

    def test_should_detect_image(self):
        """should detect image"""
        assert detect_event_type("images.generate") == "image"

    def test_should_detect_audio(self):
        """should detect audio"""
        assert detect_event_type("audio.transcriptions.create") == "audio"
        assert detect_event_type("audio.speech.create") == "audio"

    def test_should_detect_moderation(self):
        """should detect moderation"""
        assert detect_event_type("moderations.create") == "moderation"

    def test_should_return_other_for_unknown_methods(self):
        """should return other for unknown methods"""
        assert detect_event_type("unknown.method") == "other"


class TestGetApiType:
    """Tests for getApiType - exact match of TypeScript tests."""

    def test_should_normalize_chat_completions_create(self):
        """should normalize chat.completions.create"""
        assert get_api_type("chat.completions.create") == "chat.completions"

    def test_should_normalize_messages_create(self):
        """should normalize messages.create"""
        assert get_api_type("messages.create") == "messages"

    def test_should_normalize_responses_create(self):
        """should normalize responses.create"""
        assert get_api_type("responses.create") == "responses"

    def test_should_remove_create_suffix_from_other_methods(self):
        """should remove .create suffix from other methods"""
        assert get_api_type("embeddings.create") == "embeddings"
        assert get_api_type("images.generate") == "images.generate"
