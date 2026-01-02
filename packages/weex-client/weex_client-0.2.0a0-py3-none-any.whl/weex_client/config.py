"""
Configuration management for Weex client with Python 3.14 features.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .__version__ import __version__

# Type aliases for better readability and maintainability
type BaseURL = str
type Timeout = float
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
type Environment = Literal["development", "staging", "production"]


@dataclass(frozen=True, slots=True)
class ConnectionConfig:
    """Connection configuration with immutable behavior."""

    base_url: BaseURL = "https://api-contract.weex.com"
    websocket_url: str = "wss://api-contract.weex.com/ws/v2/streams"
    timeout: Timeout = 30.0
    max_connections: int = 20
    max_keepalive_connections: int = 10


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Retry configuration with exponential backoff."""

    max_retries: int = 3
    backoff_base: float = 0.5
    backoff_max: float = 8.0
    jitter: bool = True


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Rate limiting configuration to prevent API abuse."""

    requests_per_second: int = 10
    requests_per_minute: int = 600
    burst_size: int = 20


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Logging configuration with validation."""

    level: LogLevel = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    structured: bool = False


@dataclass(frozen=True, slots=True)
class WeexConfig:
    """
    Main configuration class.

    Simplified version for testing without pydantic.
    """

    api_key: str
    secret_key: str
    passphrase: str
    environment: Environment = "development"
    connection: ConnectionConfig = ConnectionConfig()
    retry: RetryConfig = RetryConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()
    logging: LoggingConfig = LoggingConfig()
    version: str = __version__

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-PASSPHRASE": self.passphrase,
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def get_base_url(self) -> str:
        """Get appropriate base URL for environment."""
        return self.connection.base_url

    def get_websocket_url(self) -> str:
        """Get WebSocket URL for environment."""
        return self.connection.websocket_url


def load_config() -> WeexConfig:
    """Load Weex configuration from environment."""
    env = os.getenv("WEEX_ENVIRONMENT", "development")
    # Ensure environment is valid
    if env not in ("development", "staging", "production"):
        env = "development"

    return WeexConfig(
        api_key=os.getenv("WEEX_API_KEY", ""),
        secret_key=os.getenv("WEEX_SECRET_KEY", ""),
        passphrase=os.getenv("WEEX_PASSPHRASE", ""),
        environment=env,  # type: ignore[arg-type]
    )
