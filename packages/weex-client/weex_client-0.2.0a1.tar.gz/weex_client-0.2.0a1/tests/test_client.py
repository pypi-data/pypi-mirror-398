"""
Tests for Weex Async Client.

Uses mocks to avoid real API calls and tests for comprehensive coverage.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from weex_client import WeexAsyncClient
from weex_client.config import WeexConfig
from weex_client.exceptions import (
    WEEXError,
    WEEXParseError,
    WEEXRateLimitError,
)
from weex_client.models import PlaceOrderRequest


class TestWeexAsyncClient:
    """Test cases for WeexAsyncClient."""

    @pytest.fixture
    def config(self) -> WeexConfig:
        """Create test configuration."""
        return WeexConfig(
            api_key="test_api_key",
            secret_key="test_secret_key",
            passphrase="test_passphrase",
            environment="development",  # Use valid environment
        )

    @pytest.fixture
    def client(self, config: WeexConfig) -> WeexAsyncClient:
        """Create test client."""
        return WeexAsyncClient(config)

    @pytest.mark.asyncio
    async def test_client_initialization(self, client: WeexAsyncClient) -> None:
        """Test client initialization."""
        assert client.config is not None
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client._closed is False

    @pytest.mark.asyncio
    async def test_context_manager(self, config: WeexConfig) -> None:
        """Test async context manager."""
        async with WeexAsyncClient(config) as client:
            assert client._closed is False
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_signature_generation(self, client: WeexAsyncClient) -> None:
        """Test HMAC signature generation."""
        signature = client._generate_signature(
            "GET",
            "/api/test",
            "?param=value",
            "",
        )

        assert isinstance(signature, str)
        assert len(signature) > 0
        assert signature != ""

    def test_auth_headers_building(self, client: WeexAsyncClient) -> None:
        """Test authentication headers building."""
        headers = client._build_auth_headers(
            "GET",
            "/api/test",
            "?param=value",
            "",
        )

        assert "ACCESS-KEY" in headers
        assert "ACCESS-SIGN" in headers
        assert "ACCESS-TIMESTAMP" in headers
        assert "ACCESS-PASSPHRASE" in headers
        assert headers["ACCESS-KEY"] == "test_api_key"
        assert headers["ACCESS-PASSPHRASE"] == "test_passphrase"

    def test_url_preparation(self, client: WeexAsyncClient) -> None:
        """Test URL preparation."""
        # Test full URL
        full_url, path, query = client._prepare_url(
            "https://api.example.com/test?param=value",
            None,
        )
        assert full_url == "https://api.example.com/test?param=value"
        assert path == "/test"
        assert query == "?param=value"

        # Test path with params
        full_url, path, query = client._prepare_url(
            "/api/test",
            {"param": "value"},
        )
        assert "/api/test" in full_url
        assert "param=value" in full_url
        assert path == "/api/test"

    def test_backoff_delay_calculation(self, client: WeexAsyncClient) -> None:
        """Test exponential backoff delay calculation."""
        delay_0 = client._backoff_delay(0)
        delay_1 = client._backoff_delay(1)
        delay_2 = client._backoff_delay(2)

        assert delay_0 >= client.backoff_base
        assert delay_1 > delay_0
        assert delay_2 > delay_1
        assert delay_2 <= client.backoff_max

    def test_filter_none_values(self, client: WeexAsyncClient) -> None:
        """Test filtering None values from dictionary."""
        data = {"a": 1, "b": None, "c": "test", "d": None}
        filtered = client._filter_none(data)

        assert filtered == {"a": 1, "c": "test"}
        assert "b" not in filtered
        assert "d" not in filtered

    @pytest.mark.asyncio
    async def test_request_success(self, client: WeexAsyncClient) -> None:
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"test": "value"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"test": "value"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.request("GET", "/test")

            assert result == {"code": 0, "data": {"test": "value"}}

    @pytest.mark.asyncio
    async def test_request_with_error_response(self, client: WeexAsyncClient) -> None:
        """Test request with API error response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 40001,
            "message": "Invalid credentials",
        }
        mock_response.status_code = 401
        mock_response.content = b'{"code": 40001, "message": "Invalid credentials"}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            with pytest.raises(WEEXError) as exc_info:
                await client.request("GET", "/test")

            assert "Invalid credentials" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_with_rate_limit(self, client: WeexAsyncClient) -> None:
        """Test request with rate limit error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 40030,
            "message": "Rate limit exceeded",
        }
        mock_response.status_code = 429
        mock_response.content = b'{"code": 40030, "message": "Rate limit exceeded"}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            with pytest.raises(WEEXRateLimitError) as exc_info:
                await client.request("GET", "/test")

            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_with_invalid_json(self, client: WeexAsyncClient) -> None:
        """Test request with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.status_code = 200
        mock_response.content = b"invalid json"

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            with pytest.raises(WEEXParseError):
                await client.request("GET", "/test")

    @pytest.mark.asyncio
    async def test_get_account_balance(self, client: WeexAsyncClient) -> None:
        """Test get account balance method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"balance": "1000.0"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"balance": "1000.0"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.get_account_balance()

            assert result == {"code": 0, "data": {"balance": "1000.0"}}
            # Verify that call was made with correct method, URL, and content
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert (
                call_args[1]["url"]
                == client.config.get_base_url() + "/capi/v2/account/assets"
            )
            assert call_args[1]["content"] is None

            # Verify essential headers are present (excluding timestamp-dependent ones)
            headers = call_args[1]["headers"]
            assert headers["ACCESS-KEY"] == "test_api_key"
            assert headers["ACCESS-PASSPHRASE"] == "test_passphrase"
            assert "ACCESS-SIGN" in headers
            assert "ACCESS-TIMESTAMP" in headers

    @pytest.mark.asyncio
    async def test_place_order(self, client: WeexAsyncClient) -> None:
        """Test place order method."""
        order_request = PlaceOrderRequest(
            symbol="BTCUSDT",
            client_oid="test_order_123",
            size="0.001",
            type="1",
            order_type="1",
            match_price="0",
            price="50000.0",
            preset_stop_loss_price=None,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"orderId": "12345"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"orderId": "12345"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.place_order(order_request)

            assert result == {"code": 0, "data": {"orderId": "12345"}}
            # Verify the call was made with correct method, URL, and content
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "POST"
            assert (
                call_args[1]["url"]
                == client.config.get_base_url() + "/capi/v2/order/placeOrder"
            )
            # Use model_dump to get filtered content (None values removed)
            expected_content = (
                order_request.dict()
                if hasattr(order_request, "dict")
                else order_request.__dict__
            )
            assert call_args[1]["content"] == json.dumps(expected_content)

            # Verify essential headers are present (excluding timestamp-dependent ones)
            headers = call_args[1]["headers"]
            assert headers["ACCESS-KEY"] == "test_api_key"
            assert headers["ACCESS-PASSPHRASE"] == "test_passphrase"
            assert "ACCESS-SIGN" in headers
            assert "ACCESS-TIMESTAMP" in headers

    @pytest.mark.asyncio
    async def test_cancel_order(self, client: WeexAsyncClient) -> None:
        """Test cancel order method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"orderId": "12345"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"orderId": "12345"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.cancel_order(order_id="12345")

            assert result == {"code": 0, "data": {"orderId": "12345"}}
            # Verify the call was made with correct method, URL, and content
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "POST"
            assert (
                call_args[1]["url"]
                == client.config.get_base_url() + "/capi/v2/order/cancel_order"
            )
            # Simple JSON content without filtering
            expected_content = {"orderId": "12345"}
            assert call_args[1]["content"] == json.dumps(expected_content)

            # Verify essential headers are present (excluding timestamp-dependent ones)
            headers = call_args[1]["headers"]
            assert headers["ACCESS-KEY"] == "test_api_key"
            assert headers["ACCESS-PASSPHRASE"] == "test_passphrase"
            assert "ACCESS-SIGN" in headers
            assert "ACCESS-TIMESTAMP" in headers

    @pytest.mark.asyncio
    async def test_get_ticker(self, client: WeexAsyncClient) -> None:
        """Test get ticker method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"price": "50000.0"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"price": "50000.0"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.get_ticker("BTCUSDT")

            assert result == {"code": 0, "data": {"price": "50000.0"}}
            # Verify that call was made with correct method, URL, and content
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert (
                call_args[1]["url"]
                == client.config.get_base_url()
                + "/capi/v2/market/ticker?symbol=BTCUSDT"
            )
            assert call_args[1]["content"] is None

            # Verify essential headers are present (excluding timestamp-dependent ones)
            headers = call_args[1]["headers"]
            assert headers["ACCESS-KEY"] == "test_api_key"
            assert headers["ACCESS-PASSPHRASE"] == "test_passphrase"
            assert "ACCESS-SIGN" in headers
            assert "ACCESS-TIMESTAMP" in headers

    @pytest.mark.asyncio
    async def test_close(self, client: WeexAsyncClient) -> None:
        """Test client close method."""
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()

        assert client._closed is True
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_network_error_handling(self, client: WeexAsyncClient) -> None:
        """Test network error handling."""
        mock_client = AsyncMock()
        mock_client.request.side_effect = Exception("Network error")

        with patch.object(client, "_ensure_client", return_value=mock_client):
            with pytest.raises(Exception) as exc_info:
                await client.request("GET", "/test")

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_multiple_positions(self, client: WeexAsyncClient) -> None:
        """Test get multiple positions method."""
        symbols = ["BTCUSDT", "ETHUSDT"]

        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"position": "0.001"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"position": "0.001"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            results = await client.get_multiple_positions(symbols)

            assert len(results) == 2
            assert all(
                result == {"code": 0, "data": {"position": "0.001"}}
                for result in results
            )

    @pytest.mark.asyncio
    async def test_stream_tickers(self, client: WeexAsyncClient) -> None:
        """Test stream tickers async generator."""
        symbols = ["BTCUSDT", "ETHUSDT"]

        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"price": "50000.0"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"price": "50000.0"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            ticker_stream = client.stream_tickers(symbols)
            ticker_results = []

            async for ticker in ticker_stream:
                ticker_results.append(ticker)
                if len(ticker_results) >= 2:  # Limit for testing
                    break

            assert len(ticker_results) == 2
            assert all(
                "symbol" in ticker and "ticker" in ticker for ticker in ticker_results
            )

    @pytest.mark.asyncio
    async def test_get_market_overview(self, client: WeexAsyncClient) -> None:
        """Test get market overview method."""
        symbol = "BTCUSDT"

        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"test": "value"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"test": "value"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.get_market_overview(symbol)

            assert "ticker" in result
            assert "order_book" in result
            assert "trades" in result
            assert "contracts" in result

    @pytest.mark.asyncio
    async def test_legacy_get_method(self, client: WeexAsyncClient) -> None:
        """Test legacy get method for backward compatibility."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": {"balance": "1000.0"}}
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0, "data": {"balance": "1000.0"}}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_ensure_client", return_value=mock_client):
            result = await client.get()

            assert result == {"code": 0, "data": {"balance": "1000.0"}}
