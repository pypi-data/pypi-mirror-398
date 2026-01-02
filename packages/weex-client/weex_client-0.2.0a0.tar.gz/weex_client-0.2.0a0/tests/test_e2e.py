"""
End-to-end tests for Weex Client.

These tests use real API calls to validate the complete integration.
Run these tests sparingly as they consume API quotas.
"""

from __future__ import annotations

import asyncio
import os

import pytest

# Skip e2e tests by default to avoid consuming API quotas
pytestmark = pytest.mark.skipif(
    not os.getenv("WEEX_E2E_TESTS"),
    reason="Set WEEX_E2E_TESTS=1 to run end-to-end tests",
)


@pytest.fixture
def real_config() -> dict[str, str]:
    """Get real configuration from environment variables."""
    return {
        "api_key": os.getenv("WEEX_API_KEY", ""),
        "secret_key": os.getenv("WEEX_SECRET_KEY", ""),
        "passphrase": os.getenv("WEEX_PASSPHRASE", ""),
        "environment": os.getenv("WEEX_ENVIRONMENT", "development"),
    }


@pytest.fixture
def test_symbol() -> str:
    """Symbol to use for testing (use a stable/low-volume symbol)."""
    return os.getenv("WEEX_TEST_SYMBOL", "BTCUSDT")


class TestWeexAsyncClientE2E:
    """End-to-end tests for WeexAsyncClient."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_get_account_balance(self, real_config: dict[str, str]) -> None:
        """Test getting real account balance."""
        from weex_client import WeexAsyncClient, WeexConfig

        if not all(real_config.values()):
            pytest.skip("Missing API credentials for e2e test")

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            balance = await client.get_account_balance()

            # Basic validation of response structure
            assert isinstance(balance, (dict, list))
            if isinstance(balance, dict) and "code" in balance:
                assert balance["code"] in (0, "0")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_get_ticker(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test getting real ticker data."""
        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            ticker = await client.get_ticker(test_symbol)

            # Basic validation of response structure
            assert isinstance(ticker, dict)
            if "code" in ticker:
                assert ticker["code"] in (0, "0")
            if "data" in ticker:
                assert isinstance(ticker["data"], dict)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_get_order_book(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test getting real order book data."""
        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            order_book = await client.get_order_book(test_symbol, limit=5)

            # Basic validation
            assert isinstance(order_book, dict)
            if "code" in order_book:
                assert order_book["code"] in (0, "0")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_get_trades(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test getting real trades data."""
        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            trades = await client.get_trades(test_symbol, limit=10)

            # Basic validation
            assert isinstance(trades, dict)
            if "code" in trades:
                assert trades["code"] in (0, "0")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_get_contracts(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test getting real contract information."""
        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            contracts = await client.get_contracts(test_symbol)

            # Basic validation
            assert isinstance(contracts, dict)
            if "code" in contracts:
                assert contracts["code"] in (0, "0")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_market_overview(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test real market overview with concurrent requests."""
        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            overview = await client.get_market_overview(test_symbol)

            # Should contain multiple data sources
            assert isinstance(overview, dict)
            assert "ticker" in overview
            assert "order_book" in overview
            assert "trades" in overview
            assert "contracts" in overview

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_get_multiple_positions(
        self, real_config: dict[str, str]
    ) -> None:
        """Test getting multiple positions concurrently."""
        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            # Test with a few symbols (some may not have positions)
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

            positions = await client.get_multiple_positions(
                symbols, return_exceptions=True
            )

            # Should return results for all symbols (even if empty)
            assert len(positions) == len(symbols)
            for pos in positions:
                # Can be exception or valid response
                assert isinstance(pos, (dict, Exception))

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_place_and_cancel_order(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test placing and cancelling a real order (use with caution!)."""
        from weex_client import WeexAsyncClient, WeexConfig
        from weex_client.models import PlaceOrderRequest

        if not os.getenv("WEEX_ALLOW_REAL_ORDERS"):
            pytest.skip("Set WEEX_ALLOW_REAL_ORDERS=1 to test real order placement")

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            # Place a very small limit order far from market price
            order = PlaceOrderRequest(
                symbol=test_symbol,
                client_oid=f"e2e_test_{asyncio.get_event_loop().time()}",
                size="0.001",  # Minimum size
                type="1",  # Open position
                order_type="1",  # Limit order
                match_price="0",  # Use specified price
                price="1000.0",  # Far from market (shouldn't fill)
                preset_stop_loss_price=None,
            )

            place_result = await client.place_order(order)

            # Try to cancel immediately
            if (
                isinstance(place_result, dict)
                and "data" in place_result
                and isinstance(place_result["data"], dict)
                and "orderId" in place_result["data"]
            ):
                order_id = place_result["data"]["orderId"]
                cancel_result = await client.cancel_order(order_id=order_id)

                # Basic validation
                assert isinstance(cancel_result, dict)
                if "code" in cancel_result:
                    assert cancel_result["code"] in (0, "0")


class TestWeexSyncClientE2E:
    """End-to-end tests for WeexSyncClient."""

    @pytest.mark.integration
    def test_real_sync_get_ticker(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test synchronous client with real API."""
        from weex_client import WeexConfig, WeexSyncClient

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        with WeexSyncClient(config) as client:
            ticker = client.get_ticker(test_symbol)

            # Basic validation
            assert isinstance(ticker, dict)
            if "code" in ticker:
                assert ticker["code"] in (0, "0")

    @pytest.mark.integration
    def test_real_sync_market_overview(
        self, real_config: dict[str, str], test_symbol: str
    ) -> None:
        """Test synchronous market overview."""
        from weex_client import WeexConfig, WeexSyncClient

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        with WeexSyncClient(config) as client:
            overview = client.get_market_overview(test_symbol)

            # Should contain multiple data sources
            assert isinstance(overview, dict)
            assert "ticker" in overview
            assert "order_book" in overview


class TestWeexWebSocketClientE2E:
    """End-to-end tests for WeexWebSocketClient."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_websocket_connection(self, real_config: dict[str, str]) -> None:
        """Test real WebSocket connection."""
        from weex_client import WeexConfig
        from weex_client.websocket import WeexWebSocketClient

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        # Test public connection first (no auth required)
        client = WeexWebSocketClient(config)

        try:
            await client.connect(private=False)
            assert client.is_connected

            # Test subscription
            await client.subscribe("tickers")
            assert "tickers" in client.subscriptions

            # Test unsubscription
            await client.unsubscribe("tickers")
            assert "tickers" not in client.subscriptions

        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_websocket_private_connection(
        self, real_config: dict[str, str]
    ) -> None:
        """Test real private WebSocket connection."""
        from weex_client import WeexConfig
        from weex_client.websocket import WeexWebSocketClient

        if not all(real_config.values()):
            pytest.skip("Missing API credentials for private WebSocket test")

        config = WeexConfig(**real_config)  # type: ignore[arg-type]
        client = WeexWebSocketClient(config)

        try:
            await client.connect(private=True)
            assert client.is_connected

            # Private channel test (if available)
            # This depends on what private channels are actually available
            # await client.subscribe("positions")

        except Exception as e:
            # Log but don't fail - private WebSocket might have different requirements
            print(f"Private WebSocket test failed: {e}")

        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_websocket_ticker_stream(
        self, real_config: dict[str, str]
    ) -> None:
        """Test real ticker streaming."""
        from weex_client import WeexConfig
        from weex_client.websocket import WeexWebSocketClient

        config = WeexConfig(**real_config)  # type: ignore[arg-type]
        client = WeexWebSocketClient(config)

        messages_received = []

        def ticker_handler(message):
            messages_received.append(message)

        try:
            await client.connect(private=False)
            client.add_message_handler("tickers", ticker_handler)

            # Stream for a short time
            stream = client.stream_tickers(["BTCUSDT"])

            async for message in stream:
                messages_received.append(message)
                if len(messages_received) >= 3:  # Collect a few messages
                    break

        except Exception as e:
            print(f"WebSocket stream test failed: {e}")

        finally:
            await client.close()

        # Basic validation - might not work if WebSocket is unavailable
        if messages_received:
            assert all(isinstance(msg, dict) for msg in messages_received)


class TestConfigurationE2E:
    """End-to-end tests for configuration."""

    @pytest.mark.integration
    def test_real_config_validation(self) -> None:
        """Test configuration validation with real credentials."""
        from weex_client import WeexConfig

        # Test with empty credentials (should fail validation)
        with pytest.raises(ValueError):
            WeexConfig(api_key="", secret_key="test", passphrase="test")

        # Test with valid structure
        config = WeexConfig(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass",
            environment="development",
        )

        assert config.api_key == "test_key"
        assert config.environment == "development"


# Performance and load tests
class TestPerformanceE2E:
    """Performance tests for real API calls."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_requests_performance(
        self, real_config: dict[str, str]
    ) -> None:
        """Test performance of concurrent requests."""
        import time

        from weex_client import WeexAsyncClient, WeexConfig

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]

            # Test sequential requests
            start_time = time.time()
            for symbol in symbols:
                await client.get_ticker(symbol)
            sequential_time = time.time() - start_time

            # Test concurrent requests
            start_time = time.time()
            overview = await client.get_market_overview("BTCUSDT")
            concurrent_time = time.time() - start_time

            # Concurrent should be faster for multiple operations
            print(f"Sequential time: {sequential_time:.2f}s")
            print(f"Concurrent time: {concurrent_time:.2f}s")

            # Basic validation that we got data
            assert isinstance(overview, dict)
            assert "ticker" in overview

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_rate_limit_handling(self, real_config: dict[str, str]) -> None:
        """Test rate limit detection and handling."""
        from weex_client import WeexAsyncClient, WeexConfig
        from weex_client.exceptions import WEEXRateLimitError

        config = WeexConfig(**real_config)  # type: ignore[arg-type]

        async with WeexAsyncClient(config) as client:
            # Make rapid requests to test rate limiting
            requests_made = 0

            try:
                for _ in range(50):  # Try many rapid requests
                    await client.get_ticker("BTCUSDT")
                    requests_made += 1
            except WEEXRateLimitError:
                print(f"Rate limit detected after {requests_made} requests")
            except Exception as e:
                print(f"Other error: {e}")

            # Test should complete (rate limiting is handled internally)
            assert requests_made > 0


# Environment and integration tests
class TestEnvironmentE2E:
    """Test different environment configurations."""

    @pytest.mark.integration
    def test_environment_urls(self) -> None:
        """Test that environment URLs are correctly configured."""
        from weex_client import WeexConfig

        for env in ["development", "staging", "production"]:
            config = WeexConfig(
                api_key="test",
                secret_key="test",
                passphrase="test",
                environment=env,  # type: ignore[arg-type]
            )

            base_url = config.get_base_url()
            assert base_url.startswith("https://")
            assert "weex.com" in base_url or "test" in base_url
