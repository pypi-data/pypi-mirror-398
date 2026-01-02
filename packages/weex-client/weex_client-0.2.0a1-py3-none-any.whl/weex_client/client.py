"""
Weex Client - Modern async-first Weex API client for Python 3.14+.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json as json_module
import time
from collections.abc import AsyncGenerator
from typing import Any, Self
from urllib.parse import urlencode, urlsplit

import httpx
import structlog

from .config import WeexConfig
from .exceptions import (
    WEEXError,
    WEEXNetworkError,
    WEEXParseError,
    WEEXRateLimitError,
    WEEXSystemError,
)
from .models import PlaceOrderRequest
from .types import ClientOrderId, Headers, OrderId, Symbol, Timeout

logger = structlog.get_logger()

# Type aliases for better type safety and readability
type ResponseData = dict[str, Any] | list[Any] | None

# Constants
DEFAULT_TIMEOUT: Timeout = 30.0
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_BACKOFF_BASE: float = 0.5
DEFAULT_BACKOFF_MAX: float = 8.0
STEP_SIZE_BTC: float = 0.0001  # for cmt_btcusdt


class WeexAsyncClient:
    """
    Modern async-first Weex API client for Python 3.14+.

    Key Features:
    - **Self type** in __aenter__ for type safety
    - **TaskGroup** for concurrent operations (Python 3.11+)
    - **Enhanced pattern matching** for error handling
    - **Structured logging** with contextual information
    - **Type safety** with strict typing
    - **Resource management** with automatic cleanup
    - **Rate limiting** with built-in detection
    """

    def __init__(
        self,
        config: WeexConfig,
        *,
        timeout: Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        backoff_max: float = DEFAULT_BACKOFF_MAX,
    ) -> None:
        """
        Initialize WeexAsyncClient with configuration.

        Python 3.14 improvements:
        - Better type inference
        - Enhanced error context
        - Improved resource management
        """
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max

        self._client: httpx.AsyncClient | None = None
        self._closed = False

        logger.info(
            "WeexAsyncClient initialized",
            timeout=timeout,
            max_retries=max_retries,
            environment=config.environment,
        )

    async def __aenter__(self) -> Self:
        """
        Async context manager entry with Python 3.14 Self type.

        Ensures proper resource initialization and cleanup.
        """
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Async context manager exit with proper cleanup.

        Python 3.14 enhances exception handling in async contexts.
        """
        self._closed = True
        if self._client is not None:
            await self._client.aclose()
            self._client = None

        if exc_type is not None:
            logger.error(
                "WeexAsyncClient context exited with error",
                exc_type=exc_type.__name__,
                exc=str(exc),
            )

    async def _ensure_client(self) -> httpx.AsyncClient:
        """
        Ensure httpx client exists with proper configuration.

        Creates client with timeout and connection limits.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_connections=self.config.connection.max_connections,
                    max_keepalive_connections=self.config.connection.max_keepalive_connections,
                ),
                follow_redirects=True,
            )
            logger.debug("Created new httpx.AsyncClient")
        return self._client

    def _generate_signature(
        self,
        method: str,
        request_path: str,
        query_string: str,
        body: str,
    ) -> str:
        """Generate HMAC SHA256 signature for Weex API."""
        timestamp = str(int(time.time() * 1000))

        if method.upper() == "GET":
            message = timestamp + method.upper() + request_path + query_string
        else:
            message = timestamp + method.upper() + request_path + query_string + body

        signature = hmac.new(
            self.config.secret_key.encode(), message.encode(), hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode()

    def _build_auth_headers(
        self,
        method: str,
        request_path: str,
        query_string: str,
        body: str,
    ) -> Headers:
        """Build authentication headers for API requests."""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(method, request_path, query_string, body)

        return {
            "ACCESS-KEY": self.config.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.config.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US",
        }

    def _prepare_url(
        self,
        url_or_path: str,
        params: dict[str, Any] | None,
    ) -> tuple[str, str, str]:
        """Prepare URL, path, and query string for API requests."""
        if url_or_path.startswith(("http://", "https://")):
            parsed = urlsplit(url_or_path)
            base = f"{parsed.scheme}://{parsed.netloc}"
            path = parsed.path
            query = parsed.query
        else:
            base = self.config.get_base_url().rstrip("/")
            path = url_or_path.split("?", 1)[0]
            query = url_or_path.split("?", 1)[1] if "?" in url_or_path else ""

        if params:
            extra = urlencode(params, doseq=True)
            query = f"{query}&{extra}" if query else extra

        query_string = f"?{query}" if query else ""
        full_url = f"{base}{path}{query_string}"

        return full_url, path, query_string

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = self.backoff_base * (2**attempt)
        return min(delay, self.backoff_max)

    def _filter_none(self, values: dict[str, Any]) -> dict[str, Any]:
        """Filter None values from dictionary."""
        return {key: value for key, value in values.items() if value is not None}

    async def _request_with_retries(
        self,
        method: str,
        full_url: str,
        request_path: str,
        query_string: str,
        headers: Headers,
        body: str,
        params: dict[str, Any] | None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        attempt = 0
        while True:
            try:
                client = await self._ensure_client()

                response = await client.request(
                    method=method,
                    url=full_url,
                    headers=headers,
                    content=body if method.upper() != "GET" else None,
                )

                # Parse and validate response
                try:
                    data = response.json()
                except ValueError as exc:
                    raise WEEXParseError(
                        "Invalid JSON response",
                        data={
                            "status_code": response.status_code,
                            "text": response.text[:500],
                        },
                    ) from exc

                # Handle API errors
                if "code" in data:
                    code = data["code"]
                    success = data.get("success")

                    if code in (0, "0") or success is True:
                        logger.info(
                            "Request successful",
                            method=method,
                            path=request_path,
                            status_code=response.status_code,
                        )
                        return response
                    else:
                        # Use pattern matching for error handling (Python 3.14 feature)
                        match (code, response.status_code):
                            case 429 | _ if code in {40030, 40031}:
                                raise WEEXRateLimitError(
                                    data.get("message", "Rate limit exceeded"),
                                    code=code,
                                    retry_after=60,
                                )
                            case _ if code in {
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
                                raise WEEXError(
                                    data.get("message", "Authentication failed"),
                                    code=code,
                                )
                            case _ if (
                                response.status_code is not None
                                and response.status_code >= 500
                            ):
                                raise WEEXSystemError(
                                    data.get("message", "System error"),
                                    code=code,
                                )
                            case _:
                                raise WEEXError(
                                    data.get("message", "API error"),
                                    code=code,
                                )

                return response

            except httpx.RequestError as exc:
                raise WEEXNetworkError(
                    f"Network error: {exc}",
                    data={"method": method, "url": full_url},
                ) from exc
            except (WEEXRateLimitError, WEEXNetworkError, WEEXSystemError) as exc:
                error = exc

            if attempt >= self.max_retries:
                raise error

            await asyncio.sleep(self._backoff_delay(attempt))
            attempt += 1

    async def request(
        self,
        method: str,
        url_or_path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: Headers | None = None,
        auth: bool = True,
        body: str | None = None,
    ) -> ResponseData:
        """
        Make API request with authentication and error handling.

        High-level interface that handles URL preparation,
        authentication, and response parsing automatically.

        Args:
            method: HTTP method
            url_or_path: API endpoint or full URL
            params: Query parameters
            json: JSON request body
            headers: Additional headers
            auth: Include authentication
            body: Raw request body

        Returns:
            ResponseData: Parsed JSON response

        Raises:
            Various WEEXError subclasses based on API response
        """
        full_url, request_path, query_string = self._prepare_url(url_or_path, params)

        # Prepare body
        if body is None:
            if json is not None:
                body = json_module.dumps(json)
            else:
                body = ""
        else:
            body = body

        # Prepare headers
        request_headers = {"Content-Type": "application/json", "locale": "en-US"}
        if auth:
            auth_headers = self._build_auth_headers(
                method, request_path, query_string, body
            )
            request_headers.update(auth_headers)

        if headers:
            request_headers.update(headers)

        response = await self._request_with_retries(
            method=method,
            full_url=full_url,
            request_path=request_path,
            query_string=query_string,
            headers=request_headers,
            body=body,
            params=params,
        )

        return response.json() if response.content else None

    async def get_account_balance(self) -> ResponseData:
        """GET /capi/v2/account/assets - Get account balance."""
        response = await self.request("GET", "/capi/v2/account/assets")
        return response

    async def get_all_positions(self) -> ResponseData:
        """GET /capi/v2/account/position/allPosition - Get all positions."""
        response = await self.request("GET", "/capi/v2/account/position/allPosition")
        return response

    async def get_position(self, symbol: Symbol) -> ResponseData:
        """GET /capi/v2/account/position/singlePosition - Get single position."""
        params = {"symbol": symbol}
        response = await self.request(
            "GET", "/capi/v2/account/position/singlePosition", params=params
        )
        return response

    async def place_order(
        self,
        order_request: PlaceOrderRequest,
    ) -> ResponseData:
        """POST /capi/v2/order/placeOrder - Place a new order."""
        logger.info("Placing order", order=order_request.dict())

        response = await self.request(
            "POST",
            "/capi/v2/order/placeOrder",
            json=order_request.dict(),
            auth=True,
        )

        logger.info("Order placed successfully", response=response)
        return response  # response is already JSON data from self.request()

    async def cancel_order(
        self,
        order_id: OrderId | None = None,
        client_oid: ClientOrderId | None = None,
    ) -> ResponseData:
        """POST /capi/v2/order/cancel_order - Cancel an order."""

        # Build request data
        data = {}
        if order_id is not None:
            data["orderId"] = order_id
        if client_oid is not None:
            data["clientOid"] = client_oid

        response = await self.request(
            "POST",
            "/capi/v2/order/cancel_order",
            json=data,
            auth=True,
        )

        return response

    async def get_all_tickers(self) -> ResponseData:
        """GET /capi/v2/market/tickers - Get all tickers."""
        response = await self.request("GET", "/capi/v2/market/tickers")
        return response

    async def get_ticker(self, symbol: Symbol) -> ResponseData:
        """GET /capi/v2/market/ticker - Get ticker for specific symbol."""
        params = {"symbol": symbol}
        response = await self.request("GET", "/capi/v2/market/ticker", params=params)
        return response

    # ========================================================================
    # Advanced Methods - Using Python 3.14 Features
    # ========================================================================

    async def get_multiple_positions(
        self,
        symbols: list[Symbol],
        *,
        return_exceptions: bool = False,
    ) -> list[dict[str, Any] | Exception]:
        """
        Get positions for multiple symbols using TaskGroup.

        Demonstrates Python 3.14's TaskGroup for concurrent operations.
        """
        logger.info(f"Getting positions for {len(symbols)} symbols")

        async with asyncio.TaskGroup() as tg:
            tasks = {
                symbol: tg.create_task(self.get_position(symbol)) for symbol in symbols
            }

            results: dict[str, ResponseData] = {}
            for symbol, task in tasks.items():
                try:
                    position = await task
                    results[symbol] = position
                except Exception as exc:
                    if return_exceptions:
                        results[symbol] = exc  # type: ignore
                    else:
                        logger.error(f"Error getting position for {symbol}: {exc}")
                        raise

        return [results.get(symbol) for symbol in symbols]  # type: ignore

    async def stream_tickers(
        self, symbols: list[Symbol]
    ) -> AsyncGenerator[dict[str, Any]]:
        """
        Stream tickers for multiple symbols using async generator.

        Python 3.14 async generator example for continuous data streaming.
        """
        logger.info(f"Streaming tickers for {len(symbols)} symbols")

        for symbol in symbols:
            ticker = await self.get_ticker(symbol)
            yield {"symbol": symbol, "ticker": ticker}

    async def get_market_overview(
        self,
        symbol: Symbol,
        *,
        order_book_limit: int = 15,
        trades_limit: int = 100,
        return_exceptions: bool = False,
    ) -> dict[str, Any]:
        """
        Get market overview with concurrent requests.

        Fetches ticker, order book, trades, and contract info concurrently.
        """
        async with asyncio.TaskGroup() as tg:
            # Create concurrent tasks
            tasks = {
                "ticker": tg.create_task(self.get_ticker(symbol)),
                "order_book": tg.create_task(
                    self.request(
                        "GET",
                        f"/capi/v2/market/depth?symbol={symbol}&limit={order_book_limit}",
                    )
                ),
                "trades": tg.create_task(
                    self.request(
                        "GET",
                        f"/capi/v2/market/trades?symbol={symbol}&limit={trades_limit}",
                    )
                ),
                "contracts": tg.create_task(
                    self.request("GET", f"/capi/v2/public/contracts?symbol={symbol}")
                ),
            }

        results: dict[str, Any] = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                if return_exceptions:
                    results[key] = e
                else:
                    raise

        return results

    async def get_order_book(self, symbol: Symbol, limit: int = 15) -> ResponseData:
        """
        GET /capi/v2/market/depth - Get order book.

        Args:
            symbol: Trading symbol
            limit: Number of price levels (default: 15)

        Returns:
            Order book data with bids and asks
        """
        params = {"symbol": symbol, "limit": limit}
        response = await self.request("GET", "/capi/v2/market/depth", params=params)
        return response

    async def get_trades(self, symbol: Symbol, limit: int = 100) -> ResponseData:
        """
        GET /capi/v2/market/trades - Get recent trades.

        Args:
            symbol: Trading symbol
            limit: Number of recent trades (default: 100)

        Returns:
            List of recent trades
        """
        params = {"symbol": symbol, "limit": limit}
        response = await self.request("GET", "/capi/v2/market/trades", params=params)
        return response

    async def get_contracts(self, symbol: Symbol | None = None) -> ResponseData:
        """
        GET /capi/v2/public/contracts - Get contract information.

        Args:
            symbol: Optional symbol to get specific contract info

        Returns:
            Contract information data
        """
        if symbol:
            params = {"symbol": symbol}
            response = await self.request(
                "GET", "/capi/v2/public/contracts", params=params
            )
        else:
            response = await self.request("GET", "/capi/v2/public/contracts")
        return response

    async def close(self) -> None:
        """Close the HTTPX client and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._closed = True
        logger.info("WeexAsyncClient closed")

    # Legacy compatibility methods (simplified wrappers around async methods)
    async def get(self) -> ResponseData:
        """Legacy method for backward compatibility."""
        return await self.get_account_balance()
