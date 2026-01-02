"""
Tests for Weex Sync Client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from weex_client import WeexConfig, WeexSyncClient
from weex_client.models import PlaceOrderRequest


class TestWeexSyncClient:
    """Test cases for WeexSyncClient."""

    @pytest.fixture
    def config(self) -> WeexConfig:
        """Create test configuration."""
        return WeexConfig(
            api_key="test_api_key",
            secret_key="test_secret_key",
            passphrase="test_passphrase",
            environment="development",
        )

    @pytest.fixture
    def client(self, config: WeexConfig) -> WeexSyncClient:
        """Create test client."""
        return WeexSyncClient(config)

    def test_client_initialization(self, client: WeexSyncClient) -> None:
        """Test client initialization."""
        assert client.config is not None
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client._closed is False

    def test_context_manager(self, config: WeexConfig) -> None:
        """Test context manager."""
        with WeexSyncClient(config) as client:
            assert client._closed is False

    @patch("weex_client.sync.asyncio.new_event_loop")
    @patch("weex_client.sync.threading.Thread")
    def test_event_loop_creation(
        self, mock_thread, mock_new_loop, client: WeexSyncClient
    ) -> None:
        """Test event loop creation in background thread."""
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_new_loop.return_value = mock_loop

        client._ensure_event_loop()

        assert client._loop is not None
        mock_thread.assert_called_once()

    @patch("weex_client.sync.asyncio.run_coroutine_threadsafe")
    def test_close(self, mock_run_coroutine, client: WeexSyncClient) -> None:
        """Test client close method."""
        # Mock event loop and thread
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = False
        client._loop = mock_loop

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        client._thread = mock_thread

        # Mock the future returned by run_coroutine_threadsafe
        mock_future = MagicMock()
        mock_future.result.return_value = None

        # Capture the coroutine passed to run_coroutine_threadsafe and close it
        def mock_run_coroutine_impl(coro, loop):
            # Close the coroutine to prevent warnings
            if hasattr(coro, "close"):
                coro.close()
            return mock_future

        mock_run_coroutine.side_effect = mock_run_coroutine_impl

        client.close()

        assert client._closed is True
        mock_run_coroutine.assert_called_once()
        mock_future.result.assert_called_once_with(timeout=5)

    @patch("weex_client.sync.asyncio.run_coroutine_threadsafe")
    def test_run_async(self, mock_run_coroutine, client: WeexSyncClient) -> None:
        """Test _run_async method."""
        mock_future = MagicMock()
        mock_future.result.return_value = "test_result"
        mock_run_coroutine.return_value = mock_future

        # Mock event loop
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = False
        client._loop = mock_loop

        result = client._run_async("test_coroutine")

        assert result == "test_result"
        mock_run_coroutine.assert_called_once_with("test_coroutine", mock_loop)

    @patch.object(WeexSyncClient, "_run_async")
    def test_get_account_balance(self, mock_run_async, client: WeexSyncClient) -> None:
        """Test get account balance method."""

        # Create a mock that properly handles the coroutine parameter
        def mock_run_async_impl(coro):
            return {"code": 0, "data": {"balance": "1000.0"}}

        mock_run_async.side_effect = mock_run_async_impl

        result = client.get_account_balance()

        assert result == {"code": 0, "data": {"balance": "1000.0"}}
        mock_run_async.assert_called_once()

        # Close the coroutine to prevent warnings
        args, kwargs = mock_run_async.call_args
        import asyncio

        if asyncio.iscoroutine(args[0]):
            args[0].close()

    @patch.object(WeexSyncClient, "_run_async")
    def test_place_order(self, mock_run_async, client: WeexSyncClient) -> None:
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

        # Create a mock that properly handles the coroutine parameter
        def mock_run_async_impl(coro):
            return {"code": 0, "data": {"orderId": "12345"}}

        mock_run_async.side_effect = mock_run_async_impl

        result = client.place_order(order_request)

        assert result == {"code": 0, "data": {"orderId": "12345"}}
        mock_run_async.assert_called_once()

        # Close the coroutine to prevent warnings
        args, kwargs = mock_run_async.call_args
        import asyncio

        if asyncio.iscoroutine(args[0]):
            args[0].close()

    @patch.object(WeexSyncClient, "_run_async")
    def test_cancel_order(self, mock_run_async, client: WeexSyncClient) -> None:
        """Test cancel order method."""

        # Create a mock that properly handles the coroutine parameter
        def mock_run_async_impl(coro):
            return {"code": 0, "data": {"orderId": "12345"}}

        mock_run_async.side_effect = mock_run_async_impl

        result = client.cancel_order(order_id="12345")

        assert result == {"code": 0, "data": {"orderId": "12345"}}
        mock_run_async.assert_called_once()

        # Close the coroutine to prevent warnings
        args, kwargs = mock_run_async.call_args
        import asyncio

        if asyncio.iscoroutine(args[0]):
            args[0].close()

    @patch.object(WeexSyncClient, "_run_async")
    def test_get_ticker(self, mock_run_async, client: WeexSyncClient) -> None:
        """Test get ticker method."""

        # Create a mock that properly handles the coroutine parameter
        def mock_run_async_impl(coro):
            return {"code": 0, "data": {"price": "50000.0"}}

        mock_run_async.side_effect = mock_run_async_impl

        result = client.get_ticker("BTCUSDT")

        assert result == {"code": 0, "data": {"price": "50000.0"}}
        mock_run_async.assert_called_once()

        # Close the coroutine to prevent warnings
        args, kwargs = mock_run_async.call_args
        import asyncio

        if asyncio.iscoroutine(args[0]):
            args[0].close()

    @patch.object(WeexSyncClient, "_run_async")
    def test_get_multiple_positions(
        self, mock_run_async, client: WeexSyncClient
    ) -> None:
        """Test get multiple positions method."""
        symbols = ["BTCUSDT", "ETHUSDT"]

        # Create a mock that properly handles the coroutine parameter
        def mock_run_async_impl(coro):
            # Just return the expected result without awaiting the coroutine
            # This prevents the coroutine from being garbage collected unawaited
            return [
                {"code": 0, "data": {"position": "0.001"}},
                {"code": 0, "data": {"position": "1.0"}},
            ]

        mock_run_async.side_effect = mock_run_async_impl

        result = client.get_multiple_positions(symbols)

        assert len(result) == 2
        mock_run_async.assert_called_once()

        # Verify that a coroutine was passed to _run_async
        args, kwargs = mock_run_async.call_args
        import asyncio

        assert asyncio.iscoroutine(args[0])
        # Close the coroutine to prevent warnings
        args[0].close()

    @patch.object(WeexSyncClient, "_run_async")
    def test_get_market_overview(self, mock_run_async, client: WeexSyncClient) -> None:
        """Test get market overview method."""

        # Create a mock that properly handles the coroutine parameter
        def mock_run_async_impl(coro):
            return {
                "ticker": {"code": 0, "data": {"price": "50000.0"}},
                "order_book": {"code": 0, "data": {"bids": []}},
                "trades": {"code": 0, "data": []},
                "contracts": {"code": 0, "data": {}},
            }

        mock_run_async.side_effect = mock_run_async_impl

        result = client.get_market_overview("BTCUSDT")

        assert "ticker" in result
        assert "order_book" in result
        assert "trades" in result
        assert "contracts" in result
        mock_run_async.assert_called_once()

        # Close the coroutine to prevent warnings
        args, kwargs = mock_run_async.call_args
        import asyncio

        if asyncio.iscoroutine(args[0]):
            args[0].close()

    @patch.object(WeexSyncClient, "_run_async")
    def test_legacy_get_method(self, mock_run_async, client: WeexSyncClient) -> None:
        """Test legacy get method for backward compatibility."""

        # Create a mock that properly handles of coroutine parameter
        def mock_run_async_impl(coro):
            return {"code": 0, "data": {"balance": "1000.0"}}

        mock_run_async.side_effect = mock_run_async_impl

        result = client.get()

        assert result == {"code": 0, "data": {"balance": "1000.0"}}
        mock_run_async.assert_called_once()

        # Close the coroutine to prevent warnings
        args, kwargs = mock_run_async.call_args
        import asyncio

        if asyncio.iscoroutine(args[0]):
            args[0].close()


class TestCreateSyncClient:
    """Test cases for create_sync_client convenience function."""

    @patch("weex_client.config.WeexConfig")
    @patch("weex_client.sync.WeexSyncClient")
    def test_create_sync_client(
        self, mock_sync_client_class, mock_config_class
    ) -> None:
        """Test create_sync_client convenience function."""
        from weex_client.sync import create_sync_client

        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        mock_client = MagicMock()
        mock_sync_client_class.return_value = mock_client

        result = create_sync_client(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass",
            environment="development",
        )

        mock_config_class.assert_called_once_with(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass",
            environment="development",  # type: ignore[arg-type]
        )
        mock_sync_client_class.assert_called_once()
        assert result == mock_client
