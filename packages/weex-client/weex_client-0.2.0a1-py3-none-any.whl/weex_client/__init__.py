"""Weex Client - Modern async-first Weex API client for Python 3.14+."""

# Core components
# Version
from .__version__ import __version__

# Client
from .client import WeexAsyncClient
from .config import WeexConfig

# Exceptions
from .exceptions import (
    WEEXAuthenticationError,
    WEEXError,
    WEEXRateLimitError,
    WEEXSystemError,
)

# Models
from .models import PlaceOrderRequest
from .sync import WeexSyncClient

# Package exports
__all__ = [
    # Configuration
    "WeexConfig",
    # Exceptions
    "WEEXError",
    "WEEXRateLimitError",
    "WEEXAuthenticationError",
    "WEEXSystemError",
    # Models
    "PlaceOrderRequest",
    # Clients
    "WeexAsyncClient",
    "WeexSyncClient",
    # Version
    "__version__",
]
