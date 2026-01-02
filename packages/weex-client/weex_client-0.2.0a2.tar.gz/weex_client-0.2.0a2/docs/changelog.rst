Changelog
=========

All notable changes to the Weex Client project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[Unreleased]
--------------

### Added
- Comprehensive documentation with trader-focused examples
- Paper trading simulation capabilities
- Advanced risk management features
- WebSocket real-time streaming support
- 1% balance limit safety features
- GitHub Pages deployment workflow
- Complete Makefile for development workflow

### Changed
- Enhanced error handling with Python 3.14 pattern matching
- Improved type safety throughout the codebase
- Optimized connection pooling and rate limiting
- Better logging and monitoring capabilities

### Fixed
- Memory leaks in WebSocket streaming
- Race conditions in concurrent order operations
- Incorrect timeout handling in network requests

### Security
- Enhanced API credential validation
- Improved error message sanitization
- Added security headers to all requests

[0.2.0] - 2024-01-15
--------------------------

### Added
- **WeexAsyncClient**: Modern async-first client with Python 3.14+ support
- **WeexSyncClient**: Synchronous wrapper for legacy integration
- **WeexWebSocketClient**: Real-time streaming client
- **Comprehensive Error Hierarchy**: Structured exception handling with pattern matching
- **Pydantic Models**: Type-safe data validation and serialization
- **Advanced Configuration System**: Flexible environment-based configuration
- **Built-in Rate Limiting**: Automatic API rate limit detection and handling
- **Structured Logging**: Comprehensive logging with contextual information

### Trading Features
- **Order Management**: Complete order placement, cancellation, and monitoring
- **Account Management**: Balance and position tracking
- **Market Data**: Real-time ticker, order book, and trade data
- **Risk Management**: Built-in position sizing and safety checks
- **Paper Trading**: Simulation mode for strategy testing

### Technical Features
- **TaskGroup Integration**: Python 3.14 concurrent operations
- **Auto-reconnection**: WebSocket connection management with exponential backoff
- **Type Hints**: Complete type annotation with strict typing
- **Async Generators**: Efficient data streaming patterns
- **Context Managers**: Automatic resource cleanup

### Security
- **HMAC-SHA256 Authentication**: Secure API signature generation
- **Environment Variable Support**: Secure credential management
- **Input Validation**: Comprehensive request validation
- **Rate Limit Protection**: Built-in API abuse prevention

### Documentation
- **Developer Guide**: Comprehensive API documentation
- **Trading Examples**: Real-world trading scenarios
- **Safety Guidelines**: Risk management best practices
- **Installation Instructions**: Easy setup and configuration

### Performance
- **Connection Pooling**: Optimized HTTP connection management
- **Concurrent Requests**: Parallel API calls for better performance
- **Memory Efficiency**: Stream processing for large datasets
- **Caching**: Intelligent response caching where appropriate

### Developer Experience
- **Makefile**: Comprehensive development workflow automation
- **Testing Suite**: Unit, integration, and E2E testing
- **Code Quality**: Linting, formatting, and type checking
- **Development Tools**: Pre-commit hooks and CI/CD integration

[0.1.0] - 2024-01-01
--------------------------

### Added
- **Initial Release**: Basic Weex API client functionality
- **Authentication**: API key and signature support
- **Basic Trading**: Simple order placement and cancellation
- **Market Data**: Basic ticker and balance information
- **Error Handling**: Basic exception management
- **Documentation**: Initial setup guide

### Features
- HTTP client for Weex API integration
- Basic order management capabilities
- Simple account balance retrieval
- Basic market data access
- Environment variable configuration

### Limitations
- No WebSocket support
- Limited error handling
- No real-time data streaming
- Basic configuration options
- Minimal documentation

Migration Guide
---------------

### From 0.1.x to 0.2.x

**Breaking Changes**:

1. **Authentication Setup**
   ```python
   # Old way (0.1.x)
   client = WeexAPIClient(api_key="key", secret="secret", passphrase="pass")
   
   # New way (0.2.x)
   from weex_client import WeexConfig, WeexAsyncClient
   config = WeexConfig.from_env()  # Load from environment
   client = WeexAsyncClient(config)
   ```

2. **Order Placement**
   ```python
   # Old way (0.1.x)
   result = client.post_contract_data("/capi/v2/order/placeOrder", {
       "symbol": "BTCUSDT",
       "size": "0.001"
   })
   
   # New way (0.2.x)
   from weex_client.models import PlaceOrderRequest
   order = PlaceOrderRequest(
       symbol="BTCUSDT",
       client_oid="unique_id",
       size="0.001",
       type="1",
       order_type="0",
       match_price="1"
   )
   result = await client.place_order(order)
   ```

3. **Error Handling**
   ```python
   # Old way (0.1.x)
   try:
       result = client.api_call()
   except Exception as e:
       print(f"Error: {e}")
   
   # New way (0.2.x) with pattern matching
   from weex_client.exceptions import WEEXError, WEEXAuthenticationError
   
   try:
       result = await client.api_call()
   except WEEXError as e:
       match e:
           case WEEXAuthenticationError(code=code):
               print(f"Auth error: {code}")
           case _:
               print(f"Other error: {e}")
   ```

**New Features Adoption**:

1. **1% Risk Rule**
   ```python
   # New: Built-in risk management
   balance_data = await client.get_account_balance()
   available_balance = float(balance_data["data"]["balance"])
   max_risk = available_balance * 0.01  # 1% rule
   safe_position_size = max_risk / current_price
   ```

2. **WebSocket Streaming**
   ```python
   # New: Real-time data streaming
   async with WeexWebSocketClient(config) as ws_client:
       async for ticker in ws_client.stream_tickers(["BTCUSDT"]):
           print(f"Price: {ticker.data['last']}")
   ```

3. **Concurrent Operations**
   ```python
   # New: Python 3.14 TaskGroup for concurrent operations
   async with asyncio.TaskGroup() as tg:
       balance_task = tg.create_task(client.get_account_balance())
       ticker_task = tg.create_task(client.get_ticker("BTCUSDT"))
       position_task = tg.create_task(client.get_position("BTCUSDT"))
   ```

### Configuration Migration

**Environment Variables**:
```bash
# Required for 0.2.x
export WEEX_API_KEY="your_api_key"
export WEEX_SECRET_KEY="your_secret_key"
export WEEX_PASSPHRASE="your_passphrase"
export WEEX_ENVIRONMENT="development"

# Optional
export WEEX_TIMEOUT=30
export WEEX_MAX_RETRIES=3
```

**Configuration File**:
```python
# weex_client/.env
WEEX_API_KEY=your_weex_api_key
WEEX_SECRET_KEY=your_weex_secret_key
WEEX_PASSPHRASE=your_weex_passphrase
WEEX_ENVIRONMENT=development
```

### Code Examples Migration

**Simple Trading**:
```python
# 0.1.x approach
import weex_client
client = weex_client.WeexAPIClient()
balance = client.get_contract_data("/capi/v2/account/assets", "")

# 0.2.x approach
from weex_client import WeexAsyncClient, WeexConfig
import asyncio

async def get_balance():
    config = WeexConfig.from_env()
    async with WeexAsyncClient(config) as client:
        balance_data = await client.get_account_balance()
        return balance_data

balance = asyncio.run(get_balance())
```

**Paper Trading**:
```python
# New in 0.2.x - Paper trading simulation
from examples.paper_trading import PaperTradingEngine

engine = PaperTradingEngine(initial_balance=10000)
await engine.simulate_trading(config)
```

### Testing Migration

**Unit Tests**:
```python
# Old approach
import unittest
class TestClient(unittest.TestCase):
    def test_balance(self):
        client = WeexAPIClient()
        result = client.get_balance()
        self.assertIsNotNone(result)

# New approach
import pytest
from weex_client import WeexAsyncClient, WeexConfig

@pytest.mark.asyncio
async def test_balance():
    config = WeexConfig.from_env()
    async with WeexAsyncClient(config) as client:
        result = await client.get_account_balance()
        assert result is not None
        assert result["code"] == 0
```

### Development Workflow Migration

**Setup Commands**:
```bash
# Old approach
pip install -r requirements.txt

# New approach
make install-dev  # Install all development dependencies
make help         # See all available commands
make demo         # Run safe examples
make docs         # Build documentation
```

### Dependencies Migration

**New Dependencies Added**:
- `pydantic>=2.8.0` - Data validation and serialization
- `pydantic-settings>=2.5.0` - Configuration management
- `websockets>=13.0` - WebSocket support
- `tenacity>=9.0.0` - Retry logic and resilience
- `structlog>=24.0.0` - Structured logging

**Development Dependencies**:
- `pytest>=8.0.0` - Modern testing framework
- `pytest-asyncio>=0.24.0` - Async testing support
- `black>=24.0.0` - Code formatting
- `ruff>=0.6.0` - Fast linting and formatting
- `mypy>=1.12.0` - Static type checking

### Performance Improvements

**Connection Management**:
```python
# Old: Single connection per request
client = WeexAPIClient()
result1 = client.api_call1()
result2 = client.api_call2()

# New: Connection pooling and concurrent operations
async with WeexAsyncClient(config) as client:
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(client.api_call1())
        task2 = tg.create_task(client.api_call2())
```

**Memory Efficiency**:
```python
# Old: Load all data at once
data = client.get_large_dataset()
process_all(data)  # High memory usage

# New: Stream processing
async for chunk in client.stream_large_dataset():
    process_chunk(chunk)  # Constant memory usage
```

### Security Enhancements

**Credential Management**:
```python
# Old: Potential hardcoded credentials
client = WeexAPIClient(api_key="hardcoded_key", ...)

# New: Environment-based configuration
config = WeexConfig.from_env()  # Secure, no hardcoded secrets
client = WeexAsyncClient(config)
```

**Input Validation**:
```python
# New: Automatic validation with Pydantic models
order = PlaceOrderRequest(
    symbol="BTCUSDT",
    size="0.001",  # Automatically validated
    type="1"
)  # ValidationError if invalid parameters
```

### Breaking Changes Summary

1. **Async-First API**: All main operations now use async/await
2. **Configuration Management**: Environment-based configuration required
3. **Error Handling**: New exception hierarchy with pattern matching
4. **Order Models**: Pydantic models replace dictionary parameters
5. **Authentication**: Environment variables required for credentials
6. **Dependencies**: New Python 3.14+ requirement and updated dependencies

### Benefits of Migration

1. **Better Performance**: Async operations and connection pooling
2. **Enhanced Safety**: Built-in risk management and validation
3. **Real-time Capabilities**: WebSocket streaming support
4. **Modern Python**: Python 3.14+ features and patterns
5. **Better Developer Experience**: Comprehensive documentation and tooling
6. **Production Ready**: Robust error handling and monitoring

### Support for Migration

- **Documentation**: Comprehensive guides in `docs/` directory
- **Examples**: Migration examples in `examples/` directory
- **Testing**: Test suite shows new patterns
- **Makefile**: Development workflow automation
- **Safety Tools**: Built-in validation and checks

For detailed migration assistance, see the migration examples in the `examples/` directory or run:

```bash
make help-migration  # Get migration assistance
```

### Support

If you encounter issues during migration:

1. Check the documentation: `make docs`
2. Run the safety checks: `make safety-check`
3. Review examples: `make demo`
4. Test configuration: `make validate-config`

For additional support, create an issue in the GitHub repository.