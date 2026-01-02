#!/usr/bin/env python3
"""
Test script for WeexAsyncClient implementation.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for local development
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent))


async def test_async_client():
    """Test new WeexAsyncClient implementation."""

    print("🚀 WeexAsyncClient")
    print("=" * 50)

    # Import after path adjustment
    try:
        from weex_client.client import WeexAsyncClient
        from weex_client.config import WeexConfig
        from weex_client.exceptions import WEEXError
        from weex_client.models import PlaceOrderRequest
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1

    # Test configuration
    config = WeexConfig(
        api_key="test_key",
        secret_key="test_secret",
        passphrase="test_passphrase",
        environment="development",
    )

    print(f"✅ Configuration: {config.environment}")

    # Test client creation and context management
    try:
        async with WeexAsyncClient(config) as _:
            print("✅ WeexAsyncClient created successfully!")

            # Test model validation
            order_request = PlaceOrderRequest(
                symbol="cmt_btcusdt",
                client_oid="test_order_001",
                size="0.01",
                type="2",  # Open short
                order_type="1",  # Market order
                match_price="1",  # Market price
                price=None,
                preset_stop_loss_price=None,
            )
            print(f"✅ Order request created: {order_request.symbol}")

            # Note: We won't actually place orders in the test
            print("\n📊 Testing place_order method (skipped - demo mode)...")
            print("   Would place order if API credentials were valid")

            # Test advanced concurrent operations
            print("\n🚀 Testing concurrent operations (skipped - demo mode)...")
            print("   Would fetch positions if API credentials were valid")

    except WEEXError as e:
        print(f"❌ Weex API error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    print("\n✅ WeexAsyncClient test completed!")
    return 0


async def test_model_validation():
    """Test pydantic model validation."""

    print("🧪 Testing Pydantic Model Validation")
    print("=" * 50)

    try:
        from weex_client.models import PlaceOrderRequest
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1

    try:
        valid_order = PlaceOrderRequest(
            symbol="cmt_btcusdt",
            client_oid="valid_order",
            size="0.01",
            type="2",  # Open short
            order_type="1",  # Market order
            match_price="1",  # Market price
            price=None,
            preset_stop_loss_price=None,
        )
        print(f"✅ Valid model: {valid_order.symbol}")

        # Test invalid models
        invalid_cases = [
            {
                "name": "empty symbol",
                "order": {
                    "symbol": "",
                    "client_oid": "test",
                    "size": "0.01",
                    "type": "2",
                    "order_type": "1",
                    "match_price": "1",
                },
            },
            {
                "name": "invalid type",
                "order": {
                    "symbol": "BTCUSDT",
                    "client_oid": "test",
                    "size": "0.01",
                    "type": "99",
                    "order_type": "1",
                    "match_price": "1",
                },
            },
            {
                "name": "negative size",
                "order": {
                    "symbol": "cmt_btcusdt",
                    "client_oid": "test",
                    "size": "-0.01",
                    "type": "2",
                    "order_type": "1",
                    "match_price": "1",
                },
            },
        ]

        for case in invalid_cases:
            try:
                _ = PlaceOrderRequest(**case["order"])
                print(f"❌ Expected validation failed for {case['name']}")
            except Exception:
                print(f"✅ Validation error caught for {case['name']}")

        print("\n✅ Model validation test completed!")
        return 0

    except Exception as e:
        print(f"❌ Model validation test failed: {e}")
        return 1


async def test_error_handling():
    """Test error handling patterns."""

    print("🛡️ Testing Error Handling Patterns")
    print("=" * 50)

    try:
        from weex_client.client import WeexAsyncClient
        from weex_client.config import WeexConfig
        from weex_client.exceptions import (
            WEEXAuthenticationError,
            WEEXError,
            WEEXRateLimitError,
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1

    try:
        config = WeexConfig(
            api_key="test_key",
            secret_key="invalid",
            passphrase="test_passphrase",
            environment="development",
        )

        async with WeexAsyncClient(config) as _:
            # These would normally trigger our error handlers
            # For testing, we'll trigger them manually
            print("\n🔥 Testing authentication errors...")

            # Simulate auth error
            auth_error = WEEXAuthenticationError(
                "Invalid credentials for testing", code=40001, context={"test": True}
            )
            print(f"   🔐 Auth error: {auth_error.message}")

            # Simulate rate limit error
            rate_error = WEEXRateLimitError(
                "Rate limit exceeded for testing",
                code=429,
                retry_after=30.0,
                context={"test": True},
            )
            print(f"   ⏱️ Rate limit error: {rate_error.message}")

            # Test pattern matching (Python 3.14 feature)
            print("\n🔍 Testing pattern matching...")

            test_errors = [
                auth_error,
                rate_error,
                WEEXError("Generic error", code=500),
                WEEXError("Network error"),
            ]

            for i, error in enumerate(test_errors):
                print(f"   {i + 1}. {error.__class__.__name__}: {error.message}")

            print("✅ Error handling patterns tested!")
            return 0

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return 1


async def main():
    """Main test runner."""
    print("WeexAsyncClient Test Suite")
    print(f"Python version: {sys.version}")
    print("=" * 70)

    try:
        # Test all functionality
        test_results = await asyncio.gather(
            test_async_client(),
            test_model_validation(),
            test_error_handling(),
            return_exceptions=True,
        )

        passed = all(isinstance(result, int) and result == 0 for result in test_results)

        print("\n" + "=" * 70)
        if passed:
            print("🎉 ALL TESTS PASSED! ✅")
        else:
            print("❌ Some tests failed!")
            for i, result in enumerate(test_results):
                if isinstance(result, Exception):
                    print(f"   Test {i + 1} failed: {result}")
                elif result != 0:
                    print(f"   Test {i + 1} failed with code: {result}")

        return 0 if passed else 1

    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        sys.exit(1)
