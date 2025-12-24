"""Tests for normalizer module - exact match of normalizer.test.ts"""

import pytest

from oximy.normalizer import normalize_data


class TestNormalizeData:
    """Tests for normalizeData - exact match of TypeScript tests."""

    def test_should_extract_model_info_from_request_and_response(self):
        """should extract model info from request and response"""
        request = {"model": "gpt-4o", "messages": []}
        response = {"model": "gpt-4o-2024-05-13", "choices": []}

        normalized = normalize_data(request, response, "openai", "completion")

        assert normalized["model"]["requested"] == "gpt-4o"
        assert normalized["model"]["used"] == "gpt-4o-2024-05-13"

    def test_should_extract_input_summary_from_messages(self):
        """should extract input summary from messages"""
        request = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello world"},
            ],
        }

        normalized = normalize_data(request, {}, "openai", "completion")

        assert normalized["input"]["type"] == "messages"
        assert normalized["input"]["message_count"] == 2
        assert normalized["input"]["has_system"] is True
        assert "system" in normalized["input"]["roles"]
        assert "user" in normalized["input"]["roles"]

    def test_should_extract_input_summary_from_text_input(self):
        """should extract input summary from text input"""
        request = {
            "model": "text-embedding-3-small",
            "input": "Hello world",
        }

        normalized = normalize_data(request, {}, "openai", "embedding")

        assert normalized["input"]["type"] == "text"
        assert normalized["input"]["content_length"] == 11

    def test_should_extract_input_summary_from_array_input(self):
        """should extract input summary from array input"""
        request = {
            "model": "text-embedding-3-small",
            "input": ["Hello", "World"],
        }

        normalized = normalize_data(request, {}, "openai", "embedding")

        assert normalized["input"]["type"] == "text_array"
        assert normalized["input"]["item_count"] == 2

    def test_should_extract_output_summary_from_choices(self):
        """should extract output summary from choices"""
        response = {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hi there!"},
                    "finish_reason": "stop",
                },
            ],
        }

        normalized = normalize_data({}, response, "openai", "completion")

        assert normalized["output"]["type"] == "message"
        assert normalized["output"]["choice_count"] == 1
        assert normalized["output"]["finish_reason"] == "stop"
        assert normalized["output"]["content_length"] == 9

    def test_should_detect_tool_calls_in_output(self):
        """should detect tool calls in output"""
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {"name": "get_weather", "arguments": '{"city":"NYC"}'},
                            },
                        ],
                    },
                    "finish_reason": "tool_calls",
                },
            ],
        }

        normalized = normalize_data({}, response, "openai", "completion")

        assert normalized["output"]["type"] == "tool_calls"

    def test_should_extract_tools_from_request(self):
        """should extract tools from request"""
        request = {
            "model": "gpt-4o",
            "messages": [],
            "tools": [
                {"function": {"name": "get_weather"}},
                {"function": {"name": "search"}},
            ],
        }

        normalized = normalize_data(request, {}, "openai", "completion")

        assert normalized["tools"]["available"]["count"] == 2
        assert "get_weather" in normalized["tools"]["available"]["names"]
        assert "search" in normalized["tools"]["available"]["names"]

    def test_should_extract_tool_calls_from_response(self):
        """should extract tool calls from response"""
        request = {
            "tools": [{"function": {"name": "get_weather"}}],
        }
        response = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {"name": "get_weather", "arguments": '{"city":"NYC"}'},
                            },
                        ],
                    },
                },
            ],
        }

        normalized = normalize_data(request, response, "openai", "completion")

        assert normalized["tools"]["called"]["count"] == 1
        assert normalized["tools"]["called"]["calls"][0]["name"] == "get_weather"
        assert normalized["tools"]["called"]["calls"][0]["id"] == "call_123"

    def test_should_extract_usage_from_openai_response(self):
        """should extract usage from OpenAI response"""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }

        normalized = normalize_data({}, response, "openai", "completion")

        assert normalized["usage"]["input_tokens"] == 100
        assert normalized["usage"]["output_tokens"] == 50
        assert normalized["usage"]["total_tokens"] == 150

    def test_should_extract_usage_from_anthropic_response(self):
        """should extract usage from Anthropic response"""
        response = {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
            },
        }

        normalized = normalize_data({}, response, "anthropic", "completion")

        assert normalized["usage"]["input_tokens"] == 100
        assert normalized["usage"]["output_tokens"] == 50
        assert normalized["usage"]["total_tokens"] == 150

    def test_should_extract_cached_tokens(self):
        """should extract cached tokens"""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "prompt_tokens_details": {
                    "cached_tokens": 80,
                },
            },
        }

        normalized = normalize_data({}, response, "openai", "completion")

        assert normalized["usage"]["cached_tokens"] == 80

    def test_should_handle_embedding_responses(self):
        """should handle embedding responses"""
        response = {
            "data": [
                {"embedding": [0] * 1536, "index": 0},
                {"embedding": [0] * 1536, "index": 1},
            ],
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }

        normalized = normalize_data({}, response, "openai", "embedding")

        assert normalized["output"]["type"] == "embeddings"
        assert normalized["output"]["choice_count"] == 2
        assert normalized["output"]["embedding_dimensions"] == 1536

    def test_should_handle_image_generation_responses(self):
        """should handle image generation responses"""
        response = {
            "data": [{"url": "https://example.com/image.png"}],
        }

        normalized = normalize_data({}, response, "openai", "image")

        assert normalized["output"]["type"] == "image_url"
        assert normalized["output"]["image_count"] == 1

    def test_should_handle_anthropic_content_blocks(self):
        """should handle Anthropic content blocks"""
        response = {
            "content": [
                {"type": "text", "text": "Hello there!"},
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
            },
        }

        normalized = normalize_data({}, response, "anthropic", "completion")

        assert normalized["output"]["type"] == "message"
        assert normalized["output"]["content_length"] == 12
        assert normalized["output"]["finish_reason"] == "end_turn"

    def test_should_detect_images_in_messages(self):
        """should detect images in messages"""
        request = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is this?"},
                        {"type": "image_url", "image_url": {"url": "https://..."}},
                    ],
                },
            ],
        }

        normalized = normalize_data(request, {}, "openai", "completion")

        assert normalized["input"]["has_images"] is True
