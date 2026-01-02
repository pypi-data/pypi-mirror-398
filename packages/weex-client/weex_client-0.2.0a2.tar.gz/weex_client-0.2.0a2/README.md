# Weex Client

Modern async-first Weex API client for Python 3.14+ with comprehensive WebSocket support.

## Features

- **Async-first design** built on httpx and websockets
- **Modern Python 3.14+** with strict typing and pattern matching
- **Comprehensive REST API** coverage for trading, account, and market data
- **Real-time WebSocket** streaming with automatic reconnection
- **Structured logging** with contextual information
- **Pydantic models** for request/response validation
- **Sync wrapper** for compatibility with existing code

## Quick Start

### Installation

```bash
pip install weex-client
```

### Basic Usage

```python
import asyncio
from weex_client import WeexAsyncClient, WeexConfig

async def main():
    # Initialize client with configuration
    config = WeexConfig.from_env()
    
    async with WeexAsyncClient(config) as client:
        # Get account balance
        balance = await client.get_account_balance()
        print(f"Balance: {balance}")
        
        # Get all positions
        positions = await client.get_all_positions()
        print(f"Positions: {positions}")

if __name__ == "__main__":
    asyncio.run(main())
```

### WebSocket Streaming

```python
import asyncio
from weex_client import WeexConfig
from weex_client.websocket import WeexWebSocketClient

async def stream_tickers():
    config = WeexConfig.from_env()
    
    async with WeexWebSocketClient(config) as ws:
        # Subscribe to ticker updates
        await ws.subscribe_tickers(["cmt_btcusdt", "cmt_ethusdt"])
        
        # Stream real-time updates
        async for message in ws.stream_messages():
            print(f"Ticker update: {message}")

if __name__ == "__main__":
    asyncio.run(stream_tickers())
```

### Sync Wrapper (for legacy code)

```python
from weex_client import WeexConfig, WeexSyncClient

# Synchronous interface
config = WeexConfig.from_env()
client = WeexSyncClient(config)

# Use synchronous methods
balance = client.get_account_balance()
positions = client.get_all_positions()
```

## Configuration

Set environment variables:

```bash
export WEEX_API_KEY="your_api_key"
export WEEX_SECRET_KEY="your_secret_key" 
export WEEX_PASSPHRASE="your_passphrase"
```

Or create configuration programmatically:

```python
from weex_client import WeexConfig

config = WeexConfig(
    api_key="your_api_key",
    secret_key="your_secret_key", 
    passphrase="your_passphrase",
    environment="development",  # development, staging, or production
    timeout=30.0,
    max_retries=3
)
```

## Python 3.14+ Features

This library leverages modern Python features:

- **Pattern matching** for robust error handling
- **TaskGroup** for concurrent operations
- **Self type** for improved type hints
- **Async generators** for data streaming
- **Strict typing** with runtime validation

## Configuration File

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Your Weex API Key (starts with 'weex_')
WEEX_API_KEY=your_actual_api_key_here

# Your Weex Secret Key 
WEEX_SECRET_KEY=your_actual_secret_key_here

# Your Weex API Passphrase
WEEX_PASSPHRASE=your_actual_passphrase_here

# Environment: development, staging, or production
WEEX_ENVIRONMENT=development

# Optional: Custom timeout settings (seconds)
API_TIMEOUT=30

# Optional: Enable debug logging
DEBUG=false
```

## Available Methods

### Contract API (Futures Trading)

```python
# Get position data
position_data = await client.get_contract_data(
    "/capi/v2/account/position/singlePosition", 
    "?symbol=cmt_btcusdt"
)

# Place order
order_data = await client.post_contract_data("/capi/v2/order/placeOrder", {
    "symbol": "cmt_btcusdt",
    "client_oid": "unique_order_id",
    "size": "0.01",
    "type": "1",
    "order_type": "0",
    "match_price": "1",
    "price": "80000"
})
```

### Spot API (Regular Trading)

```python
# Get account data
account_data = await client.get_spot_data("/api/v2/spot/account", "")

# Place spot order
order_data = await client.post_spot_data("/api/v2/spot/order", {
    "symbol": "btcusdt",
    "client_oid": "unique_order_id",
    "size": "0.001",
    "type": "1",
    "order_type": "0",
    "price": "50000"
})
```

## Error Handling

The client provides comprehensive error handling with Python 3.14+ pattern matching:

```python
from weex_client.exceptions import (
    WEEXError,
    WEEXRateLimitError,
    WEEXAuthenticationError,
    WEEXSystemError
)

try:
    result = await client.get_contract_data("/endpoint", "?params=data")
except WEEXError as e:
    match e:
        case WEEXAuthenticationError(code=code):
            print(f"Authentication failed: {code}")
        case WEEXRateLimitError(retry_after=delay):
            print(f"Rate limited, retry after {delay}s")
        case WEEXSystemError():
            print("System error, please try again later")
        case _:
            print(f"Unexpected error: {e}")
```

## Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
uv run pytest

# Run with markers
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m websocket     # WebSocket tests only
uv run pytest -m "not slow"    # Skip slow tests

# Run with coverage report
uv run pytest --cov=weex_client --cov-report=html
```

## Documentation

See the `/docs` directory for comprehensive documentation:

```bash
# Build documentation locally (requires dev dependencies)
cd docs && make html
```

## Project Structure

```
weex_client/
├── weex_client/           # Main package
│   ├── __init__.py        # Package exports
│   ├── client.py          # Async REST client
│   ├── sync.py            # Sync wrapper
│   ├── websocket.py       # WebSocket client
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic models
│   ├── types.py           # Type definitions
│   ├── auth.py            # Authentication utilities
│   ├── exceptions.py      # Error handling
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation source
├── pyproject.toml         # Project configuration
├── .env.example          # Environment template
└── README.md              # This file
```

## Development

```bash
# Clone repository
git clone <repository-url>
cd weex_client

# Setup development environment (requires Python 3.14+)
uv sync --dev

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_client.py::TestWeexAsyncClient::test_method_name

# Run with coverage
uv run pytest --cov=weex_client

# Run E2E tests
python run_e2e_tests.py all

# Code quality checks
uv run ruff check weex_client
uv run black weex_client
uv run mypy weex_client

# Run all quality checks in sequence
uv run ruff check weex_client && uv run black weex_client && uv run mypy weex_client
```

## License

MIT License. See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.