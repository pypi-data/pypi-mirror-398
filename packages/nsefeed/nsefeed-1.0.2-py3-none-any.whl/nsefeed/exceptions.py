"""
Custom exceptions for nsefeed library.

This module defines all custom exceptions used throughout the nsefeed library
to provide clear, actionable error messages for various failure scenarios.
"""

from __future__ import annotations


class NSEError(Exception):
    """Base exception for all nsefeed errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class NSEConnectionError(NSEError):
    """
    Raised when connection to NSE servers fails.

    This can occur due to network issues, server downtime, or when
    NSE blocks requests due to rate limiting or IP blocking.
    """

    def __init__(
        self,
        message: str = "Failed to connect to NSE servers",
        details: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message, details)


class NSEDataNotFoundError(NSEError):
    """
    Raised when requested data is not available.

    This can occur when:
    - The requested date is a holiday (NSE closed)
    - The symbol doesn't exist in the requested date range
    - Historical data for the specified period is not available
    """

    def __init__(
        self,
        message: str = "Requested data not found",
        details: str | None = None,
        symbol: str | None = None,
        date_range: tuple[str, str] | None = None,
    ) -> None:
        self.symbol = symbol
        self.date_range = date_range
        super().__init__(message, details)


class NSERateLimitError(NSEError):
    """
    Raised when NSE rate limits are exceeded.

    NSE typically allows ~3 requests per second. Exceeding this may result
    in temporary blocks or 429 responses.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        if retry_after and not details:
            details = f"Retry after {retry_after:.1f} seconds"
        super().__init__(message, details)


class NSEInvalidSymbolError(NSEError):
    """
    Raised when an invalid stock symbol is provided.

    NSE symbols follow specific naming conventions. This error is raised
    when the provided symbol doesn't match any known NSE equity.
    """

    def __init__(
        self,
        symbol: str,
        message: str | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        self.symbol = symbol
        self.suggestions = suggestions
        if message is None:
            message = f"Invalid NSE symbol: '{symbol}'"
        if suggestions:
            details = f"Did you mean: {', '.join(suggestions[:5])}?"
        else:
            details = "Please verify the symbol on nseindia.com"
        super().__init__(message, details)


class NSEInvalidDateError(NSEError):
    """
    Raised when an invalid date or date range is provided.

    This can occur when:
    - Date format is incorrect
    - Start date is after end date
    - Date is in the future
    - Date is too far in the past (before available data)
    """

    def __init__(
        self,
        message: str = "Invalid date or date range",
        details: str | None = None,
    ) -> None:
        super().__init__(message, details)


class NSESessionError(NSEError):
    """
    Raised when session management fails.

    This can occur when:
    - Cookie acquisition fails
    - Session expires and cannot be refreshed
    - Authentication issues with NSE servers
    """

    def __init__(
        self,
        message: str = "Session management failed",
        details: str | None = None,
    ) -> None:
        super().__init__(message, details)


class NSECacheError(NSEError):
    """
    Raised when cache operations fail.

    This can occur when:
    - Cache database is corrupted
    - Disk space is insufficient
    - File permissions are incorrect
    """

    def __init__(
        self,
        message: str = "Cache operation failed",
        details: str | None = None,
    ) -> None:
        super().__init__(message, details)


class NSEParseError(NSEError):
    """
    Raised when parsing NSE response data fails.

    This can occur when:
    - NSE changes their data format
    - Response is malformed or incomplete
    - Unexpected data structure received
    """

    def __init__(
        self,
        message: str = "Failed to parse NSE response",
        details: str | None = None,
        raw_data: str | None = None,
    ) -> None:
        self.raw_data = raw_data
        super().__init__(message, details)
