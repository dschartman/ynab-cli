"""Error handling utilities for YNAB CLI."""

import traceback

import httpx

from ynab_cli.context import is_debug


class YNABAPIError(Exception):
    """Base exception for YNAB API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        """
        Initialize YNAB API error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def __str__(self) -> str:
        """Return error message."""
        return self.message


class YNABAuthenticationError(YNABAPIError):
    """Exception for authentication errors (401)."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error."""
        super().__init__(message, status_code=401)


class YNABNotFoundError(YNABAPIError):
    """Exception for resource not found errors (404)."""

    def __init__(self, message: str = "Resource not found"):
        """Initialize not found error."""
        super().__init__(message, status_code=404)


class YNABNetworkError(Exception):
    """Exception for network-related errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        """
        Initialize network error.

        Args:
            message: Error message
            original_error: The original exception that caused this error
        """
        self.message = message
        self.original_error = original_error
        super().__init__(message)

    def __str__(self) -> str:
        """Return error message."""
        return self.message


def get_error_details(error: Exception) -> str:
    """
    Get detailed error information including stack trace if debug mode is enabled.

    Args:
        error: The exception to get details for

    Returns:
        Error details string (with stack trace if debug is enabled)
    """
    if is_debug():
        # In debug mode, show full stack trace
        return "".join(traceback.format_exception(type(error), error, error.__traceback__))
    else:
        # In normal mode, just show the error message
        return str(error)


def format_api_error(error: Exception) -> Exception:
    """
    Convert generic exceptions to specific YNAB error types.

    Args:
        error: The original exception

    Returns:
        A specific YNAB exception with actionable error message
    """
    # HTTP Status Errors
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code

        if status_code == 401:
            return YNABAuthenticationError(
                "Authentication failed. Your API token may be invalid or expired. "
                "Run 'ynab login' to configure a new token."
            )
        elif status_code == 403:
            return YNABAPIError(
                "Access denied. You don't have permission to access this resource.", status_code=403
            )
        elif status_code == 404:
            return YNABNotFoundError(
                "Resource not found. The requested budget, account, or transaction does not exist."
            )
        elif status_code == 429:
            return YNABAPIError(
                "Rate limit exceeded. YNAB API limits requests to 200 per hour. "
                "Please wait before making more requests.",
                status_code=429,
            )
        elif status_code >= 500:
            return YNABAPIError(
                "YNAB server error. The YNAB API is experiencing issues. Please try again later.",
                status_code=status_code,
            )
        else:
            return YNABAPIError(
                f"API request failed with status {status_code}: {error!s}", status_code=status_code
            )

    # Network Errors
    elif isinstance(error, httpx.TimeoutException):
        return YNABNetworkError(
            "Request timed out. Please check your internet connection and try again.",
            original_error=error,
        )
    elif isinstance(error, httpx.ConnectError):
        return YNABNetworkError(
            "Connection failed. Unable to reach YNAB API. Please check your internet connection.",
            original_error=error,
        )
    elif isinstance(error, httpx.RequestError):
        return YNABNetworkError(f"Network error: {error!s}", original_error=error)

    # Value Errors (invalid data)
    elif isinstance(error, ValueError):
        return YNABAPIError(f"Invalid data received: {error!s}")

    # Generic fallback
    else:
        return YNABAPIError(str(error))
