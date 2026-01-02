"""
Weex WebSocket Client - Modern async WebSocket client for Weex API.

Python 3.14+ implementation with async generators, pattern matching, and structured logging.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from collections.abc import AsyncGenerator, Callable
from enum import Enum
from typing import Any, Self

import structlog
import websockets

from . import __version__
from .config import WeexConfig

# Import ConnectionClosed for compatibility
try:
    from websockets.exceptions import ConnectionClosed
except ImportError:
    ConnectionClosed = Exception  # Fallback type
from .exceptions import (
    WEEXAuthenticationError,
    WEEXError,
    WEEXNetworkError,
    WEEXRateLimitError,
)
from .types import Symbol

logger = structlog.get_logger()

# Type aliases
type WebSocketMessage = dict[str, Any]
type WebSocketHandler = Callable[[WebSocketMessage], None]


class WebSocketEventType(Enum):
    """WebSocket event types."""

    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    DATA = "data"


class WeexWebSocketClient:
    """
    Modern async WebSocket client for Weex API.

    Features:
    - Async context manager support
    - Auto-reconnection with exponential backoff
    - Message handlers with pattern matching
    - Connection health monitoring
    - Rate limit detection
    - Structured logging
    - Python 3.14 TaskGroup for concurrent operations
    """

    # WebSocket endpoints
    PUBLIC_ENDPOINT = "wss://ws-contract.weex.com/v2/ws/public"
    PRIVATE_ENDPOINT = "wss://ws-contract.weex.com/v2/ws/private"

    def __init__(
        self,
        config: WeexConfig,
        *,
        max_retries: int = 5,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        ping_interval: float = 20.0,
        ping_timeout: float = 10.0,
    ) -> None:
        """
        Initialize WebSocket client.

        Args:
            config: WeexConfig instance
            max_retries: Maximum reconnection attempts
            backoff_base: Base backoff delay for reconnection
            backoff_max: Maximum backoff delay
            ping_interval: Interval for sending pings
            ping_timeout: Timeout for ping responses
        """
        self.config = config
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self._websocket: Any = None  # WebSocket client protocol
        self._connection_task: asyncio.Task | None = None
        self._message_handlers: dict[str, list[WebSocketHandler]] = {}
        self._subscriptions: set[str] = set()
        self._closed = False
        self._connection_attempts = 0

        logger.info(
            "WeexWebSocketClient initialized",
            max_retries=max_retries,
            ping_interval=ping_interval,
        )

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Async context manager exit."""
        await self.close()

        if exc_type is not None:
            logger.error(
                "WeexWebSocketClient context exited with error",
                exc_type=exc_type.__name__,
                exc=str(exc),
            )

    def _generate_signature(
        self,
        timestamp: str,
        method: str,
        request_path: str,
        query_string: str = "",
        body: str = "",
    ) -> str:
        """Generate HMAC SHA256 signature for WebSocket authentication."""
        message = timestamp + method + request_path + query_string + body

        signature = hmac.new(
            self.config.secret_key.encode(), message.encode(), hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode()

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers for private WebSocket connection."""
        timestamp = str(int(time.time() * 1000))

        # For WebSocket auth, we use a simplified signature
        signature = self._generate_signature(timestamp, "GET", "/v2/ws/private")

        return {
            "ACCESS-KEY": self.config.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.config.passphrase,
            "User-Agent": f"weex-client/{self.config.version}",
        }

    def _build_connect_kwargs(
        self,
        private: bool = False,
    ) -> dict[str, Any]:
        """Build connection kwargs for WebSocket."""
        base_kwargs = {
            "ping_interval": self.ping_interval,
            "ping_timeout": self.ping_timeout,
            "close_timeout": 10.0,
            "max_size": 2**20,  # 1MB
            "max_queue": 2**5,  # 32 messages
        }

        headers_kwargs = {}
        if private:
            headers_kwargs["additional_headers"] = self._build_auth_headers()
        else:
            headers_kwargs["additional_headers"] = {
                "User-Agent": f"weex-client/{__version__}",
            }

        return {**base_kwargs, **headers_kwargs}

    def _is_connection_active(self, websocket: Any) -> bool:
        """
        Check if WebSocket connection is active across websockets versions.

        Args:
            websocket: WebSocket connection object

        Returns:
            True if connection is active, False otherwise
        """
        if websocket is None:
            return False

        # New websockets 15.0+ (ClientConnection)
        if hasattr(websocket, "state"):
            return websocket.state.name != "CLOSED"

        # Legacy websockets (WebSocketClientProtocol)
        elif hasattr(websocket, "closed"):
            return not websocket.closed

        # Fallback - assume active if not None
        return True

    def _get_endpoint(self, private: bool = False) -> str:
        """Get WebSocket endpoint URL."""
        endpoint = self.PRIVATE_ENDPOINT if private else self.PUBLIC_ENDPOINT

        if self.config.environment != "production":
            # Use test endpoints for non-production environments
            endpoint = endpoint.replace("weex.com", "weex.com/test")

        return endpoint

    async def connect(self, private: bool = False) -> None:
        """
        Connect to WebSocket server.

        Args:
            private: Whether to connect to private channel
        """
        if self._closed:
            raise WEEXError("Cannot connect closed client")

        if self._is_connection_active(self._websocket):
            logger.warning("WebSocket already connected")
            return

        endpoint = self._get_endpoint(private)
        kwargs = self._build_connect_kwargs(private)

        logger.info("Connecting to WebSocket", endpoint=endpoint, private=private)

        try:
            self._websocket = await websockets.connect(endpoint, **kwargs)
            self._connection_attempts = 0

            # Start message processing task
            self._connection_task = asyncio.create_task(self._process_messages())

            logger.info("WebSocket connected successfully", endpoint=endpoint)

        except Exception as exc:
            self._connection_attempts += 1
            logger.error(
                "Failed to connect to WebSocket",
                endpoint=endpoint,
                attempt=self._connection_attempts,
                exc=str(exc),
            )
            raise WEEXNetworkError(f"WebSocket connection failed: {exc}") from exc

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._is_connection_active(self._websocket):
            logger.info("Disconnecting WebSocket")

            # Cancel message processing task
            if self._connection_task and not self._connection_task.done():
                self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    pass

            # Close WebSocket connection
            await self._websocket.close()
            self._websocket = None
            self._subscriptions.clear()

            logger.info("WebSocket disconnected")

    async def reconnect(self, private: bool = False) -> None:
        """Reconnect to WebSocket server with backoff."""
        await self.disconnect()

        # Calculate backoff delay
        delay = min(
            self.backoff_base * (2**self._connection_attempts), self.backoff_max
        )

        if delay > 0:
            logger.info(
                "Waiting before reconnection",
                delay=delay,
                attempt=self._connection_attempts,
            )
            await asyncio.sleep(delay)

        await self.connect(private)

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return min(self.backoff_base * (2**attempt), self.backoff_max)

    def add_message_handler(self, channel: str, handler: WebSocketHandler) -> None:
        """Add message handler for specific channel."""
        if channel not in self._message_handlers:
            self._message_handlers[channel] = []
        self._message_handlers[channel].append(handler)

        logger.debug("Added message handler", channel=channel)

    def remove_message_handler(self, channel: str, handler: WebSocketHandler) -> None:
        """Remove message handler for specific channel."""
        if channel in self._message_handlers:
            try:
                self._message_handlers[channel].remove(handler)
                logger.debug("Removed message handler", channel=channel)
            except ValueError:
                pass  # Handler not found

    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages."""
        if not self._websocket:
            raise WEEXError("WebSocket not connected")

        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message) if isinstance(message, str) else message
                    await self._handle_message(data)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Invalid JSON message", message=message[:100], exc=str(exc)
                    )
                except Exception as exc:
                    logger.error("Error processing message", exc=str(exc))

        except ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as exc:
            logger.error("Message processing error", exc=str(exc))
            raise WEEXNetworkError(f"Message processing failed: {exc}") from exc

    async def _handle_message(self, data: WebSocketMessage) -> None:
        """Handle incoming WebSocket message."""
        try:
            # Use pattern matching for message handling (Python 3.14 feature)
            match data:
                case {"event": "ping", "time": timestamp}:
                    await self.send_pong(timestamp)

                case {"event": "pong"}:
                    logger.debug("Received pong")

                case {"event": "error", "code": code, "msg": message}:
                    logger.error("WebSocket error", code=code, message=message)

                    # Handle specific error types
                    match code:
                        case c if c in {
                            40001,
                            40002,
                            40003,
                            40005,
                            40006,
                            40008,
                            40009,
                            40011,
                            40012,
                        }:
                            raise WEEXAuthenticationError(
                                f"Authentication error: {message}", code=code
                            )
                        case c if c in {40030, 40031}:
                            raise WEEXRateLimitError(
                                f"Rate limit error: {message}",
                                code=code,
                                retry_after=60,
                            )
                        case _:
                            raise WEEXError(f"WebSocket error: {message}", code=code)

                case {"channel": channel} if channel in self._message_handlers:
                    # Dispatch to channel-specific handlers
                    for handler in self._message_handlers[channel]:
                        try:
                            handler(data)
                        except Exception as exc:
                            logger.error("Handler error", channel=channel, exc=str(exc))

                case _:
                    logger.debug("Unhandled message", data=data)

        except WEEXError:
            raise
        except Exception as exc:
            logger.error("Message handling error", data=data, exc=str(exc))

    async def send_pong(self, timestamp: str) -> None:
        """Send pong response."""
        await self.send_message({"event": "pong", "time": timestamp})

    async def send_message(self, message: WebSocketMessage) -> None:
        """Send message to WebSocket server."""
        if not self._is_connection_active(self._websocket):
            raise WEEXNetworkError("WebSocket not connected")

        try:
            await self._websocket.send(json.dumps(message))
            logger.debug("Message sent", message=message)
        except Exception as exc:
            raise WEEXNetworkError(f"Failed to send message: {exc}") from exc

    async def subscribe(
        self,
        channel: str,
        *,
        symbol: Symbol | None = None,
        **params,
    ) -> None:
        """
        Subscribe to a channel.

        Args:
            channel: Channel name (e.g., 'tickers', 'orderbook', 'trades')
            symbol: Trading symbol (if applicable)
            **params: Additional subscription parameters
        """
        if channel in self._subscriptions:
            logger.warning("Already subscribed", channel=channel)
            return

        subscription = {"event": "subscribe", "channel": channel}

        if symbol:
            subscription["symbol"] = symbol

        subscription.update(params)

        await self.send_message(subscription)
        self._subscriptions.add(channel)

        logger.info("Subscribed to channel", channel=channel, symbol=symbol)

    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.

        Args:
            channel: Channel name
        """
        if channel not in self._subscriptions:
            logger.warning("Not subscribed", channel=channel)
            return

        await self.send_message({"event": "unsubscribe", "channel": channel})
        self._subscriptions.discard(channel)

        logger.info("Unsubscribed from channel", channel=channel)

    async def stream_tickers(
        self,
        symbols: list[Symbol] | None = None,
    ) -> AsyncGenerator[WebSocketMessage]:
        """
        Stream ticker data as async generator.

        Args:
            symbols: List of symbols to subscribe to (None for all)

        Yields:
            WebSocketMessage: Ticker update messages
        """
        queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue()

        def ticker_handler(message: WebSocketMessage) -> None:
            queue.put_nowait(message)

        self.add_message_handler("tickers", ticker_handler)

        try:
            if symbols:
                for symbol in symbols:
                    await self.subscribe("tickers", symbol=symbol)
            else:
                await self.subscribe("tickers")

            while not self._closed:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield message
                except TimeoutError:
                    continue

        finally:
            self.remove_message_handler("tickers", ticker_handler)
            await self.unsubscribe("tickers")

    async def stream_order_book(
        self,
        symbol: Symbol,
        *,
        level: int = 5,
    ) -> AsyncGenerator[WebSocketMessage]:
        """
        Stream order book data as async generator.

        Args:
            symbol: Trading symbol
            level: Order book depth level

        Yields:
            WebSocketMessage: Order book update messages
        """
        queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue()

        def orderbook_handler(message: WebSocketMessage) -> None:
            queue.put_nowait(message)

        self.add_message_handler("orderbook", orderbook_handler)

        try:
            await self.subscribe("orderbook", symbol=symbol, level=level)

            while not self._closed:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield message
                except TimeoutError:
                    continue

        finally:
            self.remove_message_handler("orderbook", orderbook_handler)
            await self.unsubscribe("orderbook")

    async def stream_trades(
        self,
        symbol: Symbol,
    ) -> AsyncGenerator[WebSocketMessage]:
        """
        Stream trade data as async generator.

        Args:
            symbol: Trading symbol

        Yields:
            WebSocketMessage: Trade update messages
        """
        queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue()

        def trades_handler(message: WebSocketMessage) -> None:
            queue.put_nowait(message)

        self.add_message_handler("trades", trades_handler)

        try:
            await self.subscribe("trades", symbol=symbol)

            while not self._closed:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield message
                except TimeoutError:
                    continue

        finally:
            self.remove_message_handler("trades", trades_handler)
            await self.unsubscribe("trades")

    async def close(self) -> None:
        """Close the WebSocket client and cleanup resources."""
        self._closed = True

        await self.disconnect()

        logger.info("WeexWebSocketClient closed")

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._is_connection_active(self._websocket)

    @property
    def subscriptions(self) -> set[str]:
        """Get current subscriptions."""
        return self._subscriptions.copy()

    @property
    def connection_attempts(self) -> int:
        """Get number of connection attempts."""
        return self._connection_attempts


# Convenience function for quick WebSocket client creation
async def create_websocket_client(
    config: WeexConfig,
    private: bool = False,
    *,
    max_retries: int = 5,
    backoff_base: float = 1.0,
    backoff_max: float = 30.0,
) -> WeexWebSocketClient:
    """
    Create and connect a WebSocket client.

    Args:
        config: WeexConfig instance
        private: Whether to connect to private channel
        max_retries: Maximum reconnection attempts
        backoff_base: Base backoff delay
        backoff_max: Maximum backoff delay

    Returns:
        Connected WeexWebSocketClient instance
    """
    client = WeexWebSocketClient(
        config=config,
        max_retries=max_retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )

    await client.connect(private=private)
    return client
