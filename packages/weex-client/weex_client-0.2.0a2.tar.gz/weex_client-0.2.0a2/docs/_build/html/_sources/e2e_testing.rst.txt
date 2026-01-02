# Weex Client E2E Testing

End-to-end testing for the Weex Client package.

## Setup

1. **Configure Environment Variables**

```bash
cd weex_client
cp .env.example .env
# Edit .env with your real API credentials
```

2. **Install Dependencies**

```bash
uv sync --dev
```

## Running E2E Tests

### Quick Start

```bash
# Run all e2e tests
./run_e2e_tests.py

# Or run specific test types
./run_e2e_tests.py async      # Only async client tests
./run_e2e_tests.py sync       # Only sync client tests
./run_e2e_tests.py websocket  # Only WebSocket tests
./run_e2e_tests.py performance # Only performance tests
```

### Using pytest directly

```bash
# Enable e2e tests
export WEEX_E2E_TESTS=1

# Run all e2e tests
pytest tests/test_e2e.py -v

# Run specific test classes
pytest tests/test_e2e.py::TestWeexAsyncClientE2E -v
pytest tests/test_e2e.py::TestWeexWebSocketClientE2E -v
```

## Test Categories

### 🔄 Async Client Tests (`TestWeexAsyncClientE2E`)
- Real API calls with WeexAsyncClient
- Account balance retrieval
- Market data fetching
- Order placement and cancellation (with safeguards)
- Concurrent request performance

### 🔄 Sync Client Tests (`TestWeexSyncClientE2E`)
- Synchronous wrapper functionality
- Background thread management
- Real API integration

### 🔌 WebSocket Tests (`TestWeexWebSocketClientE2E`)
- Public WebSocket connections
- Private authenticated connections
- Message streaming and handling
- Real-time data reception

### ⚡ Performance Tests (`TestPerformanceE2E`)
- Concurrent request benchmarking
- Rate limit handling validation
- Performance metrics collection

### ⚙️ Environment Tests (`TestEnvironmentE2E`)
- Configuration validation
- Environment URL resolution
- Environment variable handling

## Safety Features

### 🛡️ Test Safeguards

- **Default Skip**: E2E tests are skipped by default
- **Environment Variable Check**: Tests only run with `WEEX_E2E_TESTS=1`
- **API Quota Protection**: Use efficient test patterns
- **Order Safety**: Real order placement requires `WEEX_ALLOW_REAL_ORDERS=1`

### ⚠️ Warnings

- **API Quotas**: E2E tests consume real API quotas
- **Real Orders**: Order placement tests can execute real trades
- **Rate Limits**: Rapid requests may trigger rate limits
- **Public Data**: Some tests expose sensitive data in logs

## Environment Variables

| Variable | Required | Description |
|----------|-----------|-------------|
| `WEEX_API_KEY` | ✅ | Your Weex API key |
| `WEEX_SECRET_KEY` | ✅ | Your Weex secret key |
| `WEEX_PASSPHRASE` | ✅ | Your API passphrase |
| `WEEX_ENVIRONMENT` | ❌ | Environment (development/staging/production) |
| `WEEX_TEST_SYMBOL` | ❌ | Symbol for testing (default: BTCUSDT) |
| `WEEX_E2E_TESTS` | ❌ | Enable e2e tests (set to 1) |
| `WEEX_ALLOW_REAL_ORDERS` | ❌ | Allow real order placement (DANGEROUS) |

## Test Markers

- `@pytest.mark.integration` - Marks integration tests
- `@pytest.mark.slow` - Marks slow performance tests
- `@pytest.mark.skipif` - Conditional test skipping

## Troubleshooting

### Common Issues

1. **Tests Skipped**
   ```bash
   export WEEX_E2E_TESTS=1
   ```

2. **Authentication Failures**
   - Check API credentials in `.env`
   - Verify environment is correct
   - Check API key permissions

3. **WebSocket Connection Issues**
   - Verify network connectivity
   - Check firewall settings
   - Test with public channels first

4. **Rate Limit Errors**
   - Reduce concurrent requests
   - Add delays between tests
   - Monitor API quota usage

### Debug Mode

```bash
# Enable verbose output
pytest tests/test_e2e.py -v -s --tb=long

# Run with specific markers
pytest tests/test_e2e.py -v -m "integration and not slow"
```

## Performance Monitoring

E2E tests include performance monitoring:

- **Request Timing**: Measures API response times
- **Concurrent Efficiency**: Compares sequential vs concurrent performance
- **Rate Limit Detection**: Validates rate limit handling
- **Memory Usage**: Tracks memory consumption patterns

## Continuous Integration

For CI/CD environments:

```yaml
# GitHub Actions example
- name: Run E2E Tests
  env:
    WEEX_E2E_TESTS: 1
    WEEX_API_KEY: ${{ secrets.WEEX_API_KEY }}
    WEEX_SECRET_KEY: ${{ secrets.WEEX_SECRET_KEY }}
    WEEX_PASSPHRASE: ${{ secrets.WEEX_PASSPHRASE }}
  run: |
    ./run_e2e_tests.py async
```

## Best Practices

1. **Use Test Environment**: Prefer `development` environment
2. **Monitor Quotas**: Track API usage during testing
3. **Clean Up**: Always cancel test orders
4. **Rate Limiting**: Respect API rate limits
5. **Security**: Never commit credentials to version control