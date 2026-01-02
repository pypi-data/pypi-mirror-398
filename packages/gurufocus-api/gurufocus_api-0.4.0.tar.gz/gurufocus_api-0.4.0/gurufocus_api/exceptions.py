"""Custom exceptions for the GuruFocus API client."""

from typing import Any


class GuruFocusError(Exception):
    """Base exception for all GuruFocus API errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(GuruFocusError):
    """Raised when API authentication fails (invalid or missing token)."""

    pass


class RateLimitError(GuruFocusError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.retry_after = retry_after


class InvalidSymbolError(GuruFocusError):
    """Raised when an invalid stock symbol is provided."""

    def __init__(self, symbol: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"Invalid symbol: {symbol}", details)
        self.symbol = symbol


class NotFoundError(GuruFocusError):
    """Raised when a requested resource is not found."""

    pass


class APIError(GuruFocusError):
    """Raised for general API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code


class NetworkError(GuruFocusError):
    """Raised for network-related errors (timeouts, connection issues)."""

    pass


class ValidationError(GuruFocusError):
    """Raised when response data fails validation."""

    pass
