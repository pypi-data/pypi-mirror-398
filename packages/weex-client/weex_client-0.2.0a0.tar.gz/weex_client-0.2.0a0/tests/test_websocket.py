"""
Tests for Weex WebSocket Client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from weex_client import WeexConfig
from weex_client.exceptions import (
    WEEXAuthenticationError,
    WEEXError,
    WEEXNetworkError,
    WEEXRateLimitError,
)
from weex_client.websocket import WeexWebSocketClient


class TestWeexWebSocketClient:
    """Test cases for WeexWebSocketClient."""

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
    def client(self, config: WeexConfig) -> WeexWebSocketClient:
        """Create test client."""
        return WeexWebSocketClient(config)

    def test_client_initialization(self, client: WeexWebSocketClient) -> None:
        """Test client initialization."""
        assert client.config is not None
        assert client.max_retries == 5
        assert client.ping_interval == 20.0
        assert client._closed is False

    @pytest.mark.asyncio
    async def test_context_manager(self, config: WeexConfig) -> None:
        """Test async context manager."""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False

        mock_connect = AsyncMock(return_value=mock_websocket)

        with patch("weex_client.websocket.websockets.connect", mock_connect):
            with patch.object(
                WeexWebSocketClient, "_process_messages", return_value=AsyncMock()
            ):
                async with WeexWebSocketClient(config) as client:
                    assert client._closed is False

    def test_signature_generation(self, client: WeexWebSocketClient) -> None:
        """Test HMAC signature generation."""
        signature = client._generate_signature(
            "1234567890",
            "GET",
            "/v2/ws/private",
            "",
            "",
        )

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_auth_headers_building(self, client: WeexWebSocketClient) -> None:
        """Test authentication headers building."""
        headers = client._build_auth_headers()

        assert "ACCESS-KEY" in headers
        assert "ACCESS-SIGN" in headers
        assert "ACCESS-TIMESTAMP" in headers
        assert "ACCESS-PASSPHRASE" in headers
        assert headers["ACCESS-KEY"] == "test_api_key"
        assert headers["ACCESS-PASSPHRASE"] == "test_passphrase"

    def test_connect_kwargs_building(self, client: WeexWebSocketClient) -> None:
        """Test connection kwargs building."""
        kwargs = client._build_connect_kwargs(private=False)

        assert "ping_interval" in kwargs
        assert "ping_timeout" in kwargs
        assert "extra_headers" in kwargs
        assert kwargs["ping_interval"] == 20.0

        kwargs_private = client._build_connect_kwargs(private=True)
        assert "ACCESS-KEY" in kwargs_private["extra_headers"]

    def test_endpoint_selection(self, client: WeexWebSocketClient) -> None:
        """Test WebSocket endpoint selection."""
        public_endpoint = client._get_endpoint(private=False)
        private_endpoint = client._get_endpoint(private=True)

        assert "public" in public_endpoint
        assert "private" in private_endpoint

    @pytest.mark.asyncio
    async def test_connect_success(self, client: WeexWebSocketClient) -> None:
        """Test successful WebSocket connection."""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False

        mock_connect = AsyncMock(return_value=mock_websocket)

        with patch("weex_client.websocket.websockets.connect", mock_connect):
            with patch.object(client, "_process_messages", return_value=AsyncMock()):
                await client.connect()

                mock_connect.assert_called_once()
                assert client._websocket == mock_websocket
                assert client._connection_task is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, client: WeexWebSocketClient) -> None:
        """Test WebSocket connection failure."""
        with patch(
            "weex_client.websocket.websockets.connect",
            side_effect=Exception("Connection failed"),
        ):
            with pytest.raises(WEEXNetworkError) as exc_info:
                await client.connect()

            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect(self, client: WeexWebSocketClient) -> None:
        """Test WebSocket disconnection."""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        client._websocket = mock_websocket

        import asyncio

        # Create a real task for testing disconnect logic
        async def dummy_process_messages():
            try:
                await asyncio.sleep(100)  # Long running task
            except asyncio.CancelledError:
                raise  # Re-raise for proper cancellation handling

        real_task = asyncio.create_task(dummy_process_messages())
        client._connection_task = real_task

        await client.disconnect()

        mock_websocket.close.assert_called_once()
        assert client._websocket is None
        assert real_task.cancelled()

    @pytest.mark.asyncio
    async def test_reconnect(self, client: WeexWebSocketClient) -> None:
        """Test WebSocket reconnection with backoff."""
        with patch.object(client, "disconnect") as mock_disconnect:
            with patch.object(client, "connect") as mock_connect:
                with patch("asyncio.sleep") as mock_sleep:
                    client._connection_attempts = 1

                    await client.reconnect()

                    mock_disconnect.assert_called_once()
                    mock_connect.assert_called_once()
                    mock_sleep.assert_called_once()

    def test_backoff_delay_calculation(self, client: WeexWebSocketClient) -> None:
        """Test exponential backoff delay calculation."""
        delay_0 = client._calculate_backoff_delay(0)
        delay_1 = client._calculate_backoff_delay(1)
        delay_2 = client._calculate_backoff_delay(2)

        assert delay_0 >= client.backoff_base
        assert delay_1 > delay_0
        assert delay_2 > delay_1
        assert delay_2 <= client.backoff_max

    def test_message_handler_management(self, client: WeexWebSocketClient) -> None:
        """Test message handler management."""
        handler = MagicMock()

        client.add_message_handler("test_channel", handler)
        assert "test_channel" in client._message_handlers
        assert handler in client._message_handlers["test_channel"]

        client.remove_message_handler("test_channel", handler)
        assert handler not in client._message_handlers["test_channel"]

    @pytest.mark.asyncio
    async def test_message_handling_ping(self, client: WeexWebSocketClient) -> None:
        """Test ping message handling."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket

        with patch.object(client, "send_pong") as mock_send_pong:
            await client._handle_message({"event": "ping", "time": "1234567890"})

            mock_send_pong.assert_called_once_with("1234567890")

    @pytest.mark.asyncio
    async def test_message_handling_pong(self, client: WeexWebSocketClient) -> None:
        """Test pong message handling."""
        # Should not raise any errors
        await client._handle_message({"event": "pong"})

    @pytest.mark.asyncio
    async def test_message_handling_error(self, client: WeexWebSocketClient) -> None:
        """Test error message handling."""
        with pytest.raises(WEEXError) as exc_info:
            await client._handle_message(
                {"event": "error", "code": 40001, "msg": "Test error"}
            )

        assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_message_handling_auth_error(
        self, client: WeexWebSocketClient
    ) -> None:
        """Test authentication error handling."""
        with pytest.raises(WEEXAuthenticationError) as exc_info:
            await client._handle_message(
                {"event": "error", "code": 40001, "msg": "Auth failed"}
            )

        assert "Auth failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_message_handling_rate_limit(
        self, client: WeexWebSocketClient
    ) -> None:
        """Test rate limit error handling."""
        with pytest.raises(WEEXRateLimitError) as exc_info:
            await client._handle_message(
                {"event": "error", "code": 40030, "msg": "Rate limit"}
            )

        assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_message_handling_channel(self, client: WeexWebSocketClient) -> None:
        """Test channel message handling."""
        handler = MagicMock()
        client.add_message_handler("test_channel", handler)

        message = {"channel": "test_channel", "data": "test"}
        await client._handle_message(message)

        handler.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message(self, client: WeexWebSocketClient) -> None:
        """Test sending WebSocket message."""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        client._websocket = mock_websocket

        message = {"test": "message"}
        await client.send_message(message)

        mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_pong(self, client: WeexWebSocketClient) -> None:
        """Test sending pong response."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket

        with patch.object(client, "send_message") as mock_send:
            await client.send_pong("1234567890")

            mock_send.assert_called_once_with({"event": "pong", "time": "1234567890"})

    @pytest.mark.asyncio
    async def test_subscribe(self, client: WeexWebSocketClient) -> None:
        """Test subscribing to a channel."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket

        with patch.object(client, "send_message") as mock_send:
            await client.subscribe("test_channel", symbol="BTCUSDT")

            mock_send.assert_called_once_with(
                {"event": "subscribe", "channel": "test_channel", "symbol": "BTCUSDT"}
            )
            assert "test_channel" in client._subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe(self, client: WeexWebSocketClient) -> None:
        """Test unsubscribing from a channel."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket
        client._subscriptions.add("test_channel")

        with patch.object(client, "send_message") as mock_send:
            await client.unsubscribe("test_channel")

            mock_send.assert_called_once_with(
                {"event": "unsubscribe", "channel": "test_channel"}
            )
            assert "test_channel" not in client._subscriptions

    @pytest.mark.asyncio
    async def test_stream_tickers(self, client: WeexWebSocketClient) -> None:
        """Test ticker streaming."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket

        message_received = {"channel": "tickers", "data": {"price": "50000"}}

        with patch.object(client, "subscribe"):
            with patch("asyncio.Queue") as mock_queue_class:
                mock_queue = MagicMock()
                mock_queue_class.return_value = mock_queue

                # First call returns message, second call raises TimeoutError to exit loop
                mock_queue.get = AsyncMock(
                    side_effect=[message_received, TimeoutError()]
                )

                stream = client.stream_tickers(["BTCUSDT"])
                results = []

                try:
                    async for message in stream:
                        results.append(message)
                        # Break after first message to avoid infinite loop
                        break
                except TimeoutError:
                    pass

                assert len(results) == 1
                assert results[0]["channel"] == "tickers"

    @pytest.mark.asyncio
    async def test_stream_order_book(self, client: WeexWebSocketClient) -> None:
        """Test order book streaming."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket

        message_received = {"channel": "orderbook", "data": {"bids": []}}

        with patch.object(client, "subscribe"):
            with patch("asyncio.Queue") as mock_queue_class:
                mock_queue = MagicMock()
                mock_queue_class.return_value = mock_queue

                # First call returns message, second call raises TimeoutError to exit loop
                mock_queue.get = AsyncMock(
                    side_effect=[message_received, TimeoutError()]
                )

                stream = client.stream_order_book("BTCUSDT", level=5)
                results = []

                try:
                    async for message in stream:
                        results.append(message)
                        # Break after first message to avoid infinite loop
                        break
                except TimeoutError:
                    pass

                assert len(results) == 1
                assert results[0]["channel"] == "orderbook"

    @pytest.mark.asyncio
    async def test_stream_trades(self, client: WeexWebSocketClient) -> None:
        """Test trades streaming."""
        mock_websocket = AsyncMock()
        client._websocket = mock_websocket

        message_received = {"channel": "trades", "data": {"id": "1"}}

        with patch.object(client, "subscribe"):
            with patch("asyncio.Queue") as mock_queue_class:
                mock_queue = MagicMock()
                mock_queue_class.return_value = mock_queue

                # First call returns message, second call raises TimeoutError to exit loop
                mock_queue.get = AsyncMock(
                    side_effect=[message_received, TimeoutError()]
                )

                stream = client.stream_trades("BTCUSDT")
                results = []

                try:
                    async for message in stream:
                        results.append(message)
                        # Break after first message to avoid infinite loop
                        break
                except TimeoutError:
                    pass

                assert len(results) == 1
                assert results[0]["channel"] == "trades"

    @pytest.mark.asyncio
    async def test_close(self, client: WeexWebSocketClient) -> None:
        """Test client close method."""
        with patch.object(client, "disconnect") as mock_disconnect:
            await client.close()

            assert client._closed is True
            mock_disconnect.assert_called_once()

    def test_properties(self, client: WeexWebSocketClient) -> None:
        """Test client properties."""
        # Test is_connected property
        assert client.is_connected is False

        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        client._websocket = mock_websocket
        assert client.is_connected is True

        # Test subscriptions property
        client._subscriptions.add("test1")
        client._subscriptions.add("test2")
        assert client.subscriptions == {"test1", "test2"}

        # Test connection_attempts property
        client._connection_attempts = 3
        assert client.connection_attempts == 3

    @pytest.mark.asyncio
    async def test_send_message_not_connected(
        self, client: WeexWebSocketClient
    ) -> None:
        """Test sending message when not connected."""
        with pytest.raises(WEEXNetworkError) as exc_info:
            await client.send_message({"test": "message"})

        assert "WebSocket not connected" in str(exc_info.value)
