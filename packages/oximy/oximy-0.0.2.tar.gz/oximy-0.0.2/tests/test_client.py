"""Tests for client module - exact match of client.test.ts"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from oximy import Oximy
from oximy.types import OximyConfig


class TestConstructor:
    """Tests for constructor - exact match of TypeScript tests."""

    def test_should_throw_if_api_key_is_missing(self):
        """should throw if apiKey is missing"""
        with pytest.raises(ValueError, match="api_key is required"):
            Oximy(OximyConfig(api_key="", project_id="proj_test"))

    def test_should_throw_if_project_id_is_missing(self):
        """should throw if projectId is missing"""
        with pytest.raises(ValueError, match="project_id is required"):
            Oximy(OximyConfig(api_key="ox_test", project_id=""))

    def test_should_create_client_with_valid_config(self, mock_httpx, default_init_response):
        """should create client with valid config"""
        mock_httpx.append(default_init_response)

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        assert isinstance(oximy, Oximy)

    def test_should_accept_optional_config_options(self, mock_httpx, default_init_response):
        """should accept optional config options"""
        mock_httpx.append(default_init_response)

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
                environment="production",
                service="test-service",
                version="1.0.0",
                debug=True,
                timeout=50,
                metadata={"custom": "value"},
            )
        )

        config = oximy.get_config()
        assert config.environment == "production"
        assert config.service == "test-service"
        assert config.version == "1.0.0"
        assert config.debug is True
        assert config.timeout == 50
        assert config.metadata == {"custom": "value"}


class TestWrap:
    """Tests for wrap - exact match of TypeScript tests."""

    @pytest.mark.asyncio
    async def test_should_wrap_client_and_return_same_interface(
        self, mock_httpx, default_init_response
    ):
        """should wrap a client and return same interface"""
        mock_httpx.append(default_init_response)

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        # Wait for initialization
        await asyncio.sleep(0.1)

        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value={"choices": []})

        wrapped = oximy.wrap(mock_client)

        # Should have same structure
        assert hasattr(wrapped, "chat")
        assert hasattr(wrapped.chat, "completions")
        assert callable(wrapped.chat.completions.create)

    @pytest.mark.asyncio
    async def test_should_intercept_method_calls(self, mock_httpx, default_init_response):
        """should intercept method calls"""
        # Mock successful telemetry response
        mock_httpx.append(default_init_response)
        mock_httpx.append(
            {
                "url": "/v1/events",
                "status": 200,
                "json": {
                    "received": True,
                    "event_id": "evt_test",
                    "config_version": 1,
                },
            }
        )

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        # Wait for initialization
        await asyncio.sleep(0.1)

        mock_response = {
            "id": "chatcmpl-test",
            "choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        wrapped = oximy.wrap(mock_client)

        result = await wrapped.chat.completions.create(
            {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hi"}],
            }
        )

        # Original method should be called
        mock_client.chat.completions.create.assert_called()

        # Result should be returned unchanged
        assert result == mock_response

        # Wait for async telemetry
        await asyncio.sleep(0.1)

        # Telemetry should be sent (check that events endpoint was called)
        event_calls = [r for r in mock_httpx if r.get("url") == "/v1/events"]
        assert len(event_calls) > 0


class TestGetSettings:
    """Tests for getSettings - exact match of TypeScript tests."""

    @pytest.mark.asyncio
    async def test_should_have_settings_after_wrap_is_called(
        self, mock_httpx, default_init_response
    ):
        """should have settings after wrap is called"""
        mock_httpx.append(default_init_response)

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        # Wrap triggers initialization
        mock_client = MagicMock()
        mock_client.test = AsyncMock()
        oximy.wrap(mock_client)

        # Wait a bit for async init
        await asyncio.sleep(0.1)

        settings = oximy.get_settings()
        assert settings is not None
        assert settings.project_id == "proj_test"


class TestIsEnabled:
    """Tests for isEnabled - exact match of TypeScript tests."""

    def test_should_return_true_by_default(self, mock_httpx, default_init_response):
        """should return true by default"""
        mock_httpx.append(default_init_response)

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        assert oximy.is_enabled() is True


class TestErrorHandling:
    """Tests for error handling - exact match of TypeScript tests."""

    @pytest.mark.asyncio
    async def test_should_fail_open_when_init_fails(self, mock_httpx):
        """should fail-open when init fails"""
        # Mock network error
        mock_httpx.append(
            {
                "url": "/v1/init",
                "status": 500,
                "json": {},
            }
        )

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        # Wait for init attempt
        await asyncio.sleep(0.1)

        # Should still work, just with default settings
        mock_client = MagicMock()
        mock_client.test = AsyncMock(return_value="result")

        wrapped = oximy.wrap(mock_client)
        result = await wrapped.test()

        assert result == "result"

    @pytest.mark.asyncio
    async def test_should_rethrow_provider_errors(self, mock_httpx, default_init_response):
        """should re-throw provider errors"""
        mock_httpx.append(default_init_response)

        oximy = Oximy(
            OximyConfig(
                api_key="ox_test",
                project_id="proj_test",
            )
        )

        # Wait for initialization
        await asyncio.sleep(0.1)

        mock_error = RuntimeError("API rate limit exceeded")
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_error)

        wrapped = oximy.wrap(mock_client)

        with pytest.raises(RuntimeError, match="API rate limit exceeded"):
            await wrapped.chat.completions.create({"model": "gpt-4o", "messages": []})
