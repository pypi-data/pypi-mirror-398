# Installation

## Requirements

Weex Client requires Python 3.14 or higher.

## Install with pip

```bash
pip install weex-client
```

## Install with uv (recommended)

```bash
uv add weex-client
```

## Install from source

```bash
git clone https://github.com/your-username/weex-client.git
cd weex-client
uv sync
```

## Development Installation

```bash
git clone https://github.com/your-username/weex-client.git
cd weex-client
uv sync --dev
```

## Dependencies

Weex Client depends on:

- `httpx>=0.27.0` - HTTP client
- `pydantic>=2.8.0` - Data validation
- `pydantic-settings>=2.5.0` - Settings management
- `websockets>=13.0` - WebSocket support
- `tenacity>=9.0.0` - Retry logic
- `structlog>=24.0.0` - Structured logging

### Optional Dependencies

For development:
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.24.0` - Async testing support
- `pytest-mock>=3.14.0` - Mocking support
- `black>=24.0.0` - Code formatting
- `ruff>=0.6.0` - Linting
- `mypy>=1.12.0` - Type checking
- `coverage>=7.0.0` - Coverage reporting
- `pre-commit>=3.8.0` - Git hooks

For documentation:
- `sphinx>=8.0.0` - Documentation generator
- `sphinx-rtd-theme>=2.0.0` - Documentation theme
- `myst-parser>=4.0.0` - Markdown parser
- `sphinx-autodoc-typehints>=2.0.0` - Type hints in docs

## Verify Installation

```python
import weex_client

print(f"Weex Client version: {weex_client.__version__}")
```