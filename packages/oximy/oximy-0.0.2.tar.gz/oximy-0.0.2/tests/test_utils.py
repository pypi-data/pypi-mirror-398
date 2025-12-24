"""Tests for utils module - exact match of utils.test.ts"""

import pytest

from oximy.utils import (
    calculate_content_length,
    extract_hostname,
    generate_event_id,
    get_timestamp,
    is_async_iterable,
    estimate_tokens,
    truncate,
)


class TestGenerateEventId:
    """Tests for generateEventId - exact match of TypeScript tests."""

    def test_should_generate_id_with_evt_prefix(self):
        """should generate ID with evt_ prefix"""
        id_val = generate_event_id()
        assert id_val.startswith("evt_")

    def test_should_generate_25_character_id(self):
        """should generate 25 character ID (4 prefix + 21 random)"""
        id_val = generate_event_id()
        assert len(id_val) == 25

    def test_should_generate_unique_ids(self):
        """should generate unique IDs"""
        ids = set()
        for _ in range(1000):
            ids.add(generate_event_id())
        assert len(ids) == 1000

    def test_should_only_contain_url_safe_characters(self):
        """should only contain URL-safe characters"""
        import re

        id_val = generate_event_id()
        assert re.match(r"^evt_[A-Za-z0-9]+$", id_val)


class TestGetTimestamp:
    """Tests for getTimestamp - exact match of TypeScript tests."""

    def test_should_return_iso8601_timestamp(self):
        """should return ISO8601 timestamp"""
        import re

        ts = get_timestamp()
        # Python's time.strftime may produce slightly different format than JS Date.toISOString()
        # But should still be valid ISO8601
        # Accept either with microseconds or without
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts) is not None

    def test_should_return_current_time(self):
        """should return current time"""
        import time
        from datetime import datetime

        before = time.time()
        ts = get_timestamp()
        after = time.time()

        # Parse timestamp - handle both with and without microseconds
        try:
            ts_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            # Try without microseconds
            ts_clean = ts.split(".")[0] + "Z"
            ts_time = datetime.fromisoformat(ts_clean.replace("Z", "+00:00")).timestamp()

        assert ts_time >= before - 1  # Allow 1 second tolerance
        assert ts_time <= after + 1


class TestIsAsyncIterable:
    """Tests for isAsyncIterable - exact match of TypeScript tests."""

    async def test_should_return_true_for_async_generators(self):
        """should return true for async generators"""

        async def gen():
            yield 1

        assert is_async_iterable(gen()) is True

    def test_should_return_false_for_regular_arrays(self):
        """should return false for regular arrays"""
        assert is_async_iterable([1, 2, 3]) is False

    def test_should_return_false_for_none(self):
        """should return false for null"""
        assert is_async_iterable(None) is False

    def test_should_return_false_for_strings(self):
        """should return false for strings"""
        assert is_async_iterable("hello") is False

    def test_should_return_false_for_plain_objects(self):
        """should return false for plain objects"""
        assert is_async_iterable({"foo": "bar"}) is False


class TestEstimateTokens:
    """Tests for estimateTokens - exact match of TypeScript tests."""

    def test_should_estimate_4_chars_per_token(self):
        """should estimate ~4 chars per token"""
        text = "Hello world!"  # 12 chars
        estimate = estimate_tokens(text)
        assert estimate == 3  # ceil(12/4) = 3

    def test_should_handle_empty_string(self):
        """should handle empty string"""
        assert estimate_tokens("") == 0

    def test_should_handle_long_text(self):
        """should handle long text"""
        text = "a" * 1000
        assert estimate_tokens(text) == 250


class TestCalculateContentLength:
    """Tests for calculateContentLength - exact match of TypeScript tests."""

    def test_should_return_length_for_string(self):
        """should return length for string"""
        assert calculate_content_length("Hello") == 5

    def test_should_sum_lengths_for_string_array(self):
        """should sum lengths for string array"""
        assert calculate_content_length(["Hello", "World"]) == 10

    def test_should_extract_text_from_content_blocks(self):
        """should extract text from content blocks"""
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        assert calculate_content_length(content) == 10

    def test_should_return_0_for_non_string_array(self):
        """should return 0 for non-string/array"""
        assert calculate_content_length(123) == 0
        assert calculate_content_length(None) == 0


class TestExtractHostname:
    """Tests for extractHostname - exact match of TypeScript tests."""

    def test_should_extract_hostname_from_url(self):
        """should extract hostname from URL"""
        assert extract_hostname("https://api.openai.com/v1") == "api.openai.com"

    def test_should_handle_urls_with_ports(self):
        """should handle URLs with ports"""
        assert extract_hostname("http://localhost:11434") == "localhost"

    def test_should_return_none_for_invalid_urls(self):
        """should return null for invalid URLs"""
        assert extract_hostname("not-a-url") is None


class TestTruncate:
    """Tests for truncate - exact match of TypeScript tests."""

    def test_should_not_truncate_short_strings(self):
        """should not truncate short strings"""
        assert truncate("Hello", 10) == "Hello"

    def test_should_truncate_long_strings_with_ellipsis(self):
        """should truncate long strings with ellipsis"""
        assert truncate("Hello World!", 8) == "Hello..."

    def test_should_handle_exact_length(self):
        """should handle exact length"""
        assert truncate("Hello", 5) == "Hello"
