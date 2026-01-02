"""
Type aliases for Weex client.

This module provides type aliases for better type hint readability
and maintainability across the weex_client package.

Python 3.14 advantages:
- Enhanced type inference with union types
- Better static analysis support
- Improved IDE autocomplete
- Cleaner refactoring capabilities
"""

from typing import Any, Literal

# Trading and Order Types
type Symbol = str
type OrderId = str
type ClientOrderId = str
type Size = str
type Price = str

# Position and Trading
type Side = Literal["long", "short"]
type OrderType = Literal["1", "2", "3", "4"]  # Market/Open/Close
type ExecutionType = Literal["0", "1", "2", "3"]  # Limit/Market/etc.
type MarginMode = Literal["1", "3"]  # Cross/Isolated
type TimeInForce = Literal["0", "1", "2"]  # GTC/IOC/FOK

# API Types
type ErrorCode = int | str
type ErrorMessage = str
type ContextInfo = dict[str, Any] | None
type RequestId = str | None

# WebSocket Types
type WebSocketMessage = dict[str, Any]
type SubscriptionType = Literal["tickers", "trades", "orderbook", "positions"]

# HTTP Types
type Headers = dict[str, str]
type Timeout = float

# Response Types
type ApiResponseData = dict[str, Any] | list[Any] | None
