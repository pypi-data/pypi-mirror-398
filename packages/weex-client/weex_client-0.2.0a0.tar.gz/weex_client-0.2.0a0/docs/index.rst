# Weex Client Documentation

Welcome to Weex Client documentation! This is a modern async-first Weex API client for Python 3.14+.

## Quick Start

```python
import asyncio
from weex_client import WeexAsyncClient, WeexConfig

async def main():
    # Configure the client
    config = WeexConfig(
        api_key="your_api_key",
        secret_key="your_secret_key", 
        passphrase="your_passphrase",
        environment="development"
    )
    
    # Use async context manager
    async with WeexAsyncClient(config) as client:
        # Get account balance
        balance = await client.get_account_balance()
        print(f"Balance: {balance}")
        
        # Place an order
        from weex_client.models import PlaceOrderRequest
        order = PlaceOrderRequest(
            symbol="BTCUSDT",
            client_oid="my_order_001",
            size="0.001",
            type="1",
            order_type="1", 
            match_price="0",
            price="50000.0"
        )
        
        result = await client.place_order(order)
        print(f"Order placed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- **Async-first design** - Built for Python 3.14+ with async/await
- **Modern Python features** - Uses latest Python 3.14 features like TaskGroup and pattern matching
- **Type safety** - Full type hints and validation with Pydantic
- **Automatic retries** - Built-in exponential backoff and retry logic
- **Structured logging** - Comprehensive logging with context
- **WebSocket support** - Real-time streaming of market data
- **Sync wrapper** - Synchronous interface available for legacy code

## Table of Contents

```{toctree}
:maxdepth: 2
:caption: Contents:

install
quickstart
e2e_testing
api/config
api/client
api/sync
api/websocket
api/models
api/exceptions
examples
changelog
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`