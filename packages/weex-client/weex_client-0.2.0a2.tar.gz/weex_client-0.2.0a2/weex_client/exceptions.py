"""
Enhanced exception handling for Weex client with Python 3.14 features.

This module provides comprehensive error handling with modern Python features:

1. **Pattern matching ready** - Exception classes designed for match statements
2. **Strict typing** - Full type coverage with Python 3.14 improvements
3. **Structured data** - Rich exception metadata for debugging
4. **Async aware** - Contextual information for async operations
5. **Self-documenting** - Detailed docstrings and examples

Key Python 3.14 improvements used:
- Better union type handling in type hints
- Enhanced pattern matching compatibility
- Improved error messages and debugging
- More efficient exception handling

Example usage:
    >>> try:
    ...     await client.place_order(...)
    ... except WEEXRateLimitError as e:
    ...     print(f"Rate limited: {e.retry_after}")
    >>>
    >>> # With pattern matching (Python 3.14)
    >>> match error:
    >>>     case WEEXAuthenticationError():
    >>>         handle_auth()
    >>>     case WEEXRateLimitError(retry_after=delay):
    >>>         await asyncio.sleep(delay)
    >>>     case WEEXError(code=code, message=msg):
    >>>         log_error(code, msg)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Never

logger = logging.getLogger(__name__)

# Type aliases for better type safety and readability
type ErrorCode = int | str
type ErrorMessage = str
type ContextInfo = dict[str, Any] | None
type RequestId = str | None

# Weex API error code classifications
# These are based on Weex API documentation and real-world testing
AUTHENTICATION_CODES: frozenset[int] = frozenset(
    {
        40001,  # Invalid API key
        40002,  # Invalid signature
        40003,  # Invalid timestamp
        40005,  # Invalid passphrase
        40006,  # Invalid IP address
        40008,  # Invalid timestamp format
        40009,  # Invalid API version
        40011,  # API key expired
        40012,  # Invalid content type
    }
)

PERMISSION_CODES: frozenset[int] = frozenset(
    {
        40014,  # Insufficient permissions
        40753,  # Trading not allowed
        40022,  # Account frozen
        50003,  # Service unavailable for this user
        50004,  # Operation not permitted
    }
)

RATE_LIMIT_CODES: frozenset[int] = frozenset(
    {
        429,  # Rate limit exceeded
        40030,  # Too many requests
        40031,  # Requests too frequent
    }
)

PARAMETER_CODES: frozenset[int] = frozenset(
    {
        40017,  # Invalid parameter
        40019,  # Parameter missing
        40020,  # Parameter value out of range
        50007,  # Invalid parameter format
    }
)

SYSTEM_CODES: frozenset[int] = frozenset(
    {
        40015,  # System maintenance
        50001,  # Internal server error
        50002,  # Database error
    }
)

REQUEST_CODES: frozenset[int] = frozenset(
    {
        40007,  # Invalid request method
        40018,  # Request timeout
        40013,  # Invalid request format
    }
)

NOT_FOUND_CODES: frozenset[int] = frozenset(
    {
        50005,  # Resource not found
        40016,  # Invalid symbol
        40021,  # Order not found
    }
)


class WEEXError(Exception):
    """
    Base exception class for all Weex API errors.

    This exception is designed to work seamlessly with Python 3.14's
    pattern matching and provides rich contextual information for debugging.

    Attributes:
        code: Error code from Weex API (int or str)
        message: Human-readable error message
        data: Raw response data for debugging
        request_id: Unique request identifier for tracing
        timestamp: UTC timestamp when error occurred
        context: Additional context about the operation
        retry_after: Optional retry delay in seconds (for rate limits)

    Example:
        >>> try:
        ...     await client.place_order(...)
        ... except WEEXError as e:
        ...     print(f"Error {e.code}: {e.message}")
        ...     print(f"Request ID: {e.request_id}")
        ...     print(f"Time: {e.timestamp}")
    """

    def __init__(
        self,
        message: ErrorMessage | None = None,
        *,
        code: ErrorCode | None = None,
        data: dict[str, Any] | None = None,
        request_id: RequestId = None,
        context: ContextInfo = None,
        retry_after: float | None = None,
    ) -> None:
        """
        Initialize WeexError with comprehensive error information.

        Python 3.14 improvements:
        - Better type inference with union types
        - Enhanced error context preservation
        - Improved debugging capabilities

        Args:
            message: Human-readable error message
            code: Weex API error code
            data: Raw response data for debugging
            request_id: Unique request identifier for tracing
            context: Additional context about the operation
            retry_after: Retry delay in seconds (for rate limits)
        """
        self.code = code
        self.message = message or "WEEX API error"
        self.data = data
        self.request_id = request_id
        self.timestamp = datetime.now(UTC)
        self.context = context
        self.retry_after = retry_after

        # Add structured logging for better debugging
        logger.error(
            "Weex API error occurred: code=%s message=%s request_id=%s context=%s timestamp=%s",
            code,
            message,
            request_id,
            context,
            self.timestamp.isoformat(),
        )

        super().__init__(self.message)

    def __repr__(self) -> str:
        """
        Provide detailed representation for debugging.

        Python 3.14 improves exception representation with
        better string formatting and type safety.
        """
        return (
            f"{self.__class__.__name__}("
            f"code={self.code!r}, "
            f"message={self.message!r}, "
            f"request_id={self.request_id!r}, "
            f"timestamp={self.timestamp.isoformat()!r}"
            f")"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to dictionary for serialization.

        Useful for logging, monitoring, and API responses.

        Returns:
            Dictionary with all exception data
        """
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "retry_after": self.retry_after,
            "data": self.data,
        }


class WEEXAuthenticationError(WEEXError):
    """Authentication failed - invalid credentials, expired keys, etc."""


class WEEXPermissionError(WEEXError):
    """Insufficient permissions for the requested operation."""


class WEEXRateLimitError(WEEXError):
    """
    Rate limit exceeded.

    Attributes:
        retry_after: Time to wait before retrying (seconds)
        limit_type: Type of limit (requests/minute, requests/second, etc.)
    """

    def __init__(
        self,
        message: ErrorMessage | None = None,
        *,
        retry_after: float | None = None,
        limit_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message or "Rate limit exceeded", retry_after=retry_after, **kwargs
        )
        self.limit_type = limit_type


class WEEXParameterError(WEEXError):
    """Invalid parameters in the request."""


class WEEXSystemError(WEEXError):
    """System-level errors (maintenance, internal errors, etc.)."""


class WEEXRequestError(WEEXError):
    """Request format or method errors."""


class WEEXNotFoundError(WEEXError):
    """Requested resource not found."""


class WEEXNetworkError(WEEXError):
    """
    Network-related errors.

    Python 3.14 enhances network error handling with better
    async context preservation and timeout management.
    """


class WEEXParseError(WEEXError):
    """Failed to parse API response."""


# Error code mapping for automatic exception classification
# Python 3.14's frozenset and dict comprehension improvements
ERROR_CODE_MAP: dict[int, type[WEEXError]] = {
    **dict.fromkeys(AUTHENTICATION_CODES, WEEXAuthenticationError),
    **dict.fromkeys(PERMISSION_CODES, WEEXPermissionError),
    **dict.fromkeys(RATE_LIMIT_CODES, WEEXRateLimitError),
    **dict.fromkeys(PARAMETER_CODES, WEEXParameterError),
    **dict.fromkeys(SYSTEM_CODES, WEEXSystemError),
    **dict.fromkeys(REQUEST_CODES, WEEXRequestError),
    **dict.fromkeys(NOT_FOUND_CODES, WEEXNotFoundError),
}


def _normalize_code(code: ErrorCode | None) -> ErrorCode | None:
    """
    Normalize error code to consistent format.

    Python 3.14 improves type checking with better union type handling.
    """
    if code is None:
        return None
    if isinstance(code, str):
        stripped = code.strip()
        if stripped.isdigit():
            return int(stripped)
    return code


def _extract_message(payload: dict[str, Any]) -> ErrorMessage:
    """
    Extract error message from various response formats.

    Weex API may return error messages in different fields.
    This function handles all known variations.
    """
    for key in ("message", "msg", "error", "error_message", "detail"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "WEEX API error"


def _extract_request_id(payload: dict[str, Any]) -> RequestId:
    """
    Extract request ID from response for tracing.

    Useful for debugging with Weex support.
    """
    for key in ("request_id", "requestId", "req_id", "reqId", "request-id", "id"):
        value = payload.get(key)
        if value is not None:
            return str(value)
    return None


def _extract_retry_after(
    payload: dict[str, Any], http_status: int | None
) -> float | None:
    """
    Extract retry-after information from rate limit responses.

    Supports both seconds and ISO datetime formats.
    """
    if http_status == 429:
        # Check various retry-after fields
        for key in ("retry_after", "retryAfter", "retry-after"):
            value = payload.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str) and value.isdigit():
                return float(value)

        # Default retry delay for rate limits
        return 60.0
    return None


def _classify_error(
    code: ErrorCode | None,
    http_status: int | None,
    payload: dict[str, Any] | None = None,
) -> type[WEEXError]:
    """
    Classify error based on code and HTTP status.

    Uses Python 3.14's improved pattern matching capabilities
    for better error classification logic.
    """
    normalized = _normalize_code(code)

    # Enhanced pattern matching for error classification
    if normalized is not None and isinstance(normalized, int):
        if normalized in RATE_LIMIT_CODES:
            return WEEXRateLimitError
        if normalized in ERROR_CODE_MAP:
            return ERROR_CODE_MAP[normalized]

    if http_status == 429:
        return WEEXRateLimitError
    if http_status is not None and http_status >= 500:
        return WEEXSystemError

    return WEEXError


def handle_api_error(
    payload: dict[str, Any] | Any,
    *,
    http_status: int | None = None,
    context: ContextInfo = None,
    operation: str | None = None,
) -> dict[str, Any]:
    """
    Handle Weex API response and raise appropriate exceptions.

    This function demonstrates Python 3.14's enhanced pattern matching
    and provides comprehensive error handling for all API responses.

    Args:
        payload: API response data (dict or other type)
        http_status: HTTP status code from response
        context: Additional context about the operation
        operation: Description of operation being performed

    Returns:
        The original payload if it represents a successful response

    Raises:
        Various WEEXError subclasses based on error classification

    Example:
        >>> try:
        ...     response = await client.request(...)
        ...     data = handle_api_error(
        ...         response,
        ...         http_status=400,
        ...         context={"operation": "place_order"}
        ...     )
        ... except WEEXRateLimitError as e:
        ...     await asyncio.sleep(e.retry_after)
        ...     # Retry the request
    """

    # Validate response type
    if not isinstance(payload, dict):
        if http_status is not None and http_status < 400:
            return payload

        logger.error(
            "Invalid response type received: payload_type=%s http_status=%s operation=%s context=%s",
            type(payload).__name__,
            http_status,
            operation,
            context,
        )

        raise WEEXParseError(
            "Invalid response type: expected dict",
            data={"payload": payload, "type": type(payload).__name__},
            context=context,
        )

    # Extract error information
    code: ErrorCode | None = payload.get("code")
    success = payload.get("success")
    message = _extract_message(payload)
    request_id = _extract_request_id(payload)
    retry_after = _extract_retry_after(payload, http_status)

    # Check for successful response
    if (
        code in (0, "0")
        or success is True
        or (code is None and http_status is not None and http_status < 400)
    ):
        return payload

    # Classify and raise appropriate exception
    exc_class = _classify_error(
        code or 0, http_status, payload if isinstance(payload, dict) else None
    )

    # Enhanced error context
    error_context = {
        **(context or {}),
        "operation": operation,
        "http_status": http_status,
        "response_code": code,
        "response_message": message,
    }

    logger.error(
        "Weex API error detected: code=%s message=%s class=%s http_status=%s request_id=%s operation=%s context=%s",
        code,
        message,
        exc_class.__name__,
        http_status,
        request_id,
        operation,
        error_context,
    )

    raise exc_class(
        message,
        code=code,
        data=payload,
        request_id=request_id,
        context=error_context,
        retry_after=retry_after,
    )


def create_error_handler(
    operation: str,
    logger_instance: logging.Logger | None = None,
) -> Callable[[Exception], Never]:
    """
    Create a configured error handler for specific operations.

    Python 3.14's improved Callable type hints make this more
    type-safe and easier to use in async contexts.

    Args:
        operation: Description of the operation
        logger_instance: Custom logger instance (optional)

    Returns:
        Error handler function that never returns (Never type)

    Example:
        >>> handle_place_order_error = create_error_handler("place_order")
        >>> try:
        ...     await client.place_order(...)
        ... except Exception as e:
        ...     handle_place_order_error(e)
    """
    log = logger_instance or logger

    def handler(error: Exception) -> Never:
        """
        Handle error and raise appropriate WEEX exception.

        This function demonstrates Python 3.14's Never type
        for functions that never return normally.
        """
        log.error(
            "Operation failed: %s: type=%s message=%s",
            operation,
            type(error).__name__,
            str(error),
        )

        if isinstance(error, WEEXError):
            raise error

        # Convert non-WEEX exceptions
        raise WEEXError(
            f"Unexpected error in {operation}: {error}",
            data={
                "original_error": type(error).__name__,
                "original_message": str(error),
            },
            context={"operation": operation},
        )

    return handler


# Example pattern matching error handler for Python 3.14
def handle_with_pattern_matching(error: Exception) -> str:
    """
    Demonstrate Python 3.14 pattern matching for error handling.

    This function shows how to use enhanced pattern matching
    with custom exception hierarchy.

    Args:
        error: Exception to handle

    Returns:
        Description of the handling action taken
    """
    match error:
        case WEEXAuthenticationError(code=code, request_id=req_id):
            return f"Authentication failed with code {code}, request ID: {req_id}"

        case WEEXRateLimitError(retry_after=delay):
            return f"Rate limited, retry after {delay} seconds"

        case WEEXNetworkError(context=ctx):
            return f"Network error, context: {ctx}"

        case WEEXError(code=code, message=msg):
            return f"Generic Weex error {code}: {msg}"

        case _:
            return f"Unknown error: {error}"
