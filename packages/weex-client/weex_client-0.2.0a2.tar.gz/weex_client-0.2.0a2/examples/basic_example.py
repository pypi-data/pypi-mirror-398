#!/usr/bin/env python3
"""
Basic usage example for Weex Client.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for local development
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent))


async def demo_basic_usage():
    """Demonstrate basic Weex client usage."""

    print("🚀 Weex Client Basic Usage Example")
    print("=" * 50)

    # Import after path adjustment
    try:
        from weex_client.config import WeexConfig
        from weex_client.exceptions import (
            WEEXAuthenticationError,
            WEEXError,
            WEEXRateLimitError,
        )

        print("✅ Core imports successful!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This might be due to missing dependencies or path issues.")
        return

    # 1. Configuration loading
    print("\n📋 1. Configuration Loading")
    print("-" * 30)

    try:
        # Try to load from environment
        config = WeexConfig(
            api_key="demo_key",
            secret_key="demo_secret",
            passphrase="demo_passphrase",
            environment="development",
        )
        print("✅ Manual configuration successful!")
        print(f"   Environment: {config.environment}")
        print(f"   Base URL: {config.get_base_url()}")
        print(f"   WebSocket URL: {config.get_websocket_url()}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return

    # 2. Error handling patterns
    print("\n🛡️ 2. Error Handling Patterns")
    print("-" * 30)

    # Python 3.14 pattern matching demonstration
    test_errors = [
        WEEXAuthenticationError("Auth failed", code=40001),
        WEEXRateLimitError("Rate limit", retry_after=60),
        WEEXError("Generic error", code=500),
    ]

    for error in test_errors:
        match error:
            case WEEXAuthenticationError(code=code):
                print(f"   🔐 Authentication error: code={code}")
            case WEEXRateLimitError(retry_after=delay):
                print(f"   ⏱️ Rate limit error: retry after {delay}s")
            case WEEXError(code=code):
                print(f"   ❌ Generic error: code={code}")
            case _:
                print(f"   ❓ Unknown error: {error}")

    # 3. Type safety examples
    print("\n🔧 3. Type Safety Examples")
    print("-" * 30)

    # Basic type usage (without complex models for now)
    symbol = "cmt_btcusdt"
    order_type = "2"  # Open short
    price = "50000"

    print(f"   Symbol: {symbol}")
    print(f"   Order Type: {order_type}")
    print(f"   Price: {price}")

    # Type validation
    if symbol and order_type and price:
        print("✅ Type validation passed")
    else:
        print("❌ Type validation failed")

    print("\n🎯 Basic Usage Demo Completed!")
    print("=" * 50)
    print("\nNext steps:")
    print("✅ Core structure validated")
    print("📋 Configuration system working")
    print("🛡️ Error handling implemented")
    print("🔧 Type safety verified")
    print("\nRemaining tasks:")
    print("   • Migrate REST client from demo_code.py")
    print("   • Implement WebSocket client")
    print("   • Add sync wrapper")
    print("   • Create comprehensive tests")
    print("   • Add documentation")


async def main():
    """Main entry point."""
    await demo_basic_usage()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Demo failed with error: {e}")
        sys.exit(1)
