"""
Weex Sync Client - Synchronous wrapper for async Weex client.

Provides a blocking interface for users who prefer synchronous code.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Self

import structlog

from .client import ResponseData, WeexAsyncClient
from .config import WeexConfig
from .models import PlaceOrderRequest
from .types import ClientOrderId, OrderId, Symbol, Timeout

logger = structlog.get_logger()

logger = structlog.get_logger()


class WeexSyncClient:
    """
    Synchronous wrapper for WeexAsyncClient.

    Provides a blocking interface while maintaining the benefits
    of the async implementation internally.
    """

    def __init__(
        self,
        config: WeexConfig,
        *,
        timeout: Timeout = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        backoff_max: float = 8.0,
    ) -> None:
        """
        Initialize synchronous client wrapper.

        Args:
            config: WeexConfig instance
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            backoff_base: Base backoff delay for retries
            backoff_max: Maximum backoff delay
        """
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max

        # Create async client
        self._async_client = WeexAsyncClient(
            config=config,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            backoff_max=backoff_max,
        )

        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._closed = False

        logger.info("WeexSyncClient initialized")

    def _ensure_event_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure we have an event loop running in a background thread."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_event_loop,
                daemon=True,
                name="weex-sync-loop",
            )
            self._thread.start()
            # Wait for loop to be ready
            while not self._loop.is_running():
                threading.Event().wait(0.001)
        return self._loop

    def _run_event_loop(self) -> None:
        """Run the event loop in a background thread."""
        if self._loop:
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

    def _run_async(self, coro) -> Any:
        """Run async coroutine in background thread and return result."""
        loop = self._ensure_event_loop()

        if loop.is_closed():
            raise RuntimeError("Event loop is closed")

        if threading.current_thread() == self._thread:
            # We're already in the event loop thread
            return loop.run_until_complete(coro)
        else:
            # Run in background thread
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=self.timeout + 10)

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()

    def get_account_balance(self) -> ResponseData:
        """GET /capi/v2/account/assets - Get account balance."""
        return self._run_async(self._async_client.get_account_balance())

    def get_all_positions(self) -> ResponseData:
        """GET /capi/v2/account/position/allPosition - Get all positions."""
        return self._run_async(self._async_client.get_all_positions())

    def get_position(self, symbol: Symbol) -> ResponseData:
        """GET /capi/v2/account/position/singlePosition - Get single position."""
        return self._run_async(self._async_client.get_position(symbol))

    def place_order(self, order_request: PlaceOrderRequest) -> dict[str, Any]:
        """POST /capi/v2/order/placeOrder - Place a new order."""
        return self._run_async(self._async_client.place_order(order_request))

    def cancel_order(
        self,
        order_id: OrderId | None = None,
        client_oid: ClientOrderId | None = None,
    ) -> dict[str, Any]:
        """POST /capi/v2/order/cancel_order - Cancel an order."""
        return self._run_async(
            self._async_client.cancel_order(order_id=order_id, client_oid=client_oid)
        )

    def get_all_tickers(self) -> ResponseData:
        """GET /capi/v2/market/tickers - Get all tickers."""
        return self._run_async(self._async_client.get_all_tickers())

    def get_ticker(self, symbol: Symbol) -> ResponseData:
        """GET /capi/v2/market/ticker - Get ticker for specific symbol."""
        return self._run_async(self._async_client.get_ticker(symbol))

    def get_order_book(self, symbol: Symbol, limit: int = 15) -> ResponseData:
        """GET /capi/v2/market/depth - Get order book."""
        return self._run_async(
            self._async_client.request(
                "GET", f"/capi/v2/market/depth?symbol={symbol}&limit={limit}"
            )
        )

    def get_trades(self, symbol: Symbol, limit: int = 100) -> ResponseData:
        """GET /capi/v2/market/trades - Get recent trades."""
        return self._run_async(
            self._async_client.request(
                "GET", f"/capi/v2/market/trades?symbol={symbol}&limit={limit}"
            )
        )

    def get_contracts(self, symbol: Symbol | None = None) -> ResponseData:
        """GET /capi/v2/market/contracts - Get contract information."""
        if symbol:
            return self._run_async(
                self._async_client.request(
                    "GET", f"/capi/v2/public/contracts?symbol={symbol}"
                )
            )
        else:
            return self._run_async(
                self._async_client.request("GET", "/capi/v2/public/contracts")
            )

    def get_market_overview(
        self,
        symbol: Symbol,
        *,
        order_book_limit: int = 15,
        trades_limit: int = 100,
        return_exceptions: bool = False,
    ) -> dict[str, Any]:
        """
        Get market overview with concurrent requests.

        This method showcases the power of the async implementation
        while providing a synchronous interface.
        """
        return self._run_async(
            self._async_client.get_market_overview(
                symbol,
                order_book_limit=order_book_limit,
                trades_limit=trades_limit,
                return_exceptions=return_exceptions,
            )
        )

    def get_multiple_positions(
        self,
        symbols: list[Symbol],
        *,
        return_exceptions: bool = False,
    ) -> list[dict[str, Any] | Exception]:
        """
        Get positions for multiple symbols concurrently.

        Returns results in the same order as input symbols.
        """
        return self._run_async(
            self._async_client.get_multiple_positions(
                symbols, return_exceptions=return_exceptions
            )
        )

    def close(self) -> None:
        """Close the client and cleanup resources."""
        self._closed = True

        if self._loop and not self._loop.is_closed():
            # Schedule async client cleanup
            asyncio.run_coroutine_threadsafe(
                self._async_client.close(), self._loop
            ).result(timeout=5)

            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)

            # Wait for thread to finish
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)

        logger.info("WeexSyncClient closed")

    # Legacy compatibility methods
    def get(self) -> ResponseData:
        """Legacy method for backward compatibility."""
        return self.get_account_balance()


# Convenience function for quick sync client creation
def create_sync_client(
    api_key: str,
    secret_key: str,
    passphrase: str,
    environment: str = "production",
    *,
    timeout: Timeout = 30.0,
    max_retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> WeexSyncClient:
    """
    Create a pre-configured synchronous Weex client.

    This is a convenience function for quick client creation
    without needing to create a WeexConfig instance first.

    Args:
        api_key: Your Weex API key
        secret_key: Your Weex secret key
        passphrase: Your Weex API passphrase
        environment: Environment ('production', 'sandbox', 'test')
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        backoff_base: Base backoff delay for retries
        backoff_max: Maximum backoff delay

    Returns:
        Configured WeexSyncClient instance
    """
    # Import WeexConfig with proper typing to avoid circular imports
    from .config import WeexConfig

    config = WeexConfig(
        api_key=api_key,
        secret_key=secret_key,
        passphrase=passphrase,
        environment=environment,  # type: ignore[arg-type]
    )

    return WeexSyncClient(
        config=config,
        timeout=timeout,
        max_retries=max_retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )
