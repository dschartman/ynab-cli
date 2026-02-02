"""Tests for error handling utilities."""

import httpx
import pytest
from unittest.mock import Mock

from ynab_cli.error_handling import (
    format_api_error,
    YNABAPIError,
    YNABAuthenticationError,
    YNABNotFoundError,
    YNABNetworkError,
)


class TestYNABExceptions:
    """Tests for custom YNAB exception classes."""

    def test_ynab_api_error_attributes(self):
        """YNABAPIError should store status code and message."""
        error = YNABAPIError("Test error", status_code=500)
        assert error.message == "Test error"
        assert error.status_code == 500
        assert str(error) == "Test error"

    def test_ynab_authentication_error(self):
        """YNABAuthenticationError should be a subclass of YNABAPIError."""
        error = YNABAuthenticationError("Invalid token")
        assert isinstance(error, YNABAPIError)
        assert error.status_code == 401
        assert error.message == "Invalid token"

    def test_ynab_not_found_error(self):
        """YNABNotFoundError should be a subclass of YNABAPIError."""
        error = YNABNotFoundError("Budget not found")
        assert isinstance(error, YNABAPIError)
        assert error.status_code == 404
        assert error.message == "Budget not found"

    def test_ynab_network_error(self):
        """YNABNetworkError should store original exception."""
        original = ConnectionError("Network unreachable")
        error = YNABNetworkError("Connection failed", original_error=original)
        assert error.message == "Connection failed"
        assert error.original_error is original


class TestFormatAPIError:
    """Tests for format_api_error function."""

    def test_format_401_authentication_error(self):
        """Should convert 401 HTTPStatusError to YNABAuthenticationError."""
        mock_response = Mock()
        mock_response.status_code = 401
        http_error = httpx.HTTPStatusError(
            "Unauthorized",
            request=Mock(),
            response=mock_response
        )

        result = format_api_error(http_error)

        assert isinstance(result, YNABAuthenticationError)
        assert "API token" in result.message.lower() or "authentication" in result.message.lower()

    def test_format_403_forbidden_error(self):
        """Should convert 403 HTTPStatusError to YNABAPIError."""
        mock_response = Mock()
        mock_response.status_code = 403
        http_error = httpx.HTTPStatusError(
            "Forbidden",
            request=Mock(),
            response=mock_response
        )

        result = format_api_error(http_error)

        assert isinstance(result, YNABAPIError)
        assert result.status_code == 403
        assert "permission" in result.message.lower() or "access" in result.message.lower()

    def test_format_404_not_found_error(self):
        """Should convert 404 HTTPStatusError to YNABNotFoundError."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response
        )

        result = format_api_error(http_error)

        assert isinstance(result, YNABNotFoundError)
        assert "not found" in result.message.lower()

    def test_format_429_rate_limit_error(self):
        """Should convert 429 HTTPStatusError to YNABAPIError with rate limit message."""
        mock_response = Mock()
        mock_response.status_code = 429
        http_error = httpx.HTTPStatusError(
            "Too Many Requests",
            request=Mock(),
            response=mock_response
        )

        result = format_api_error(http_error)

        assert isinstance(result, YNABAPIError)
        assert result.status_code == 429
        assert "rate limit" in result.message.lower()

    def test_format_500_server_error(self):
        """Should convert 500 HTTPStatusError to YNABAPIError."""
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Internal Server Error",
            request=Mock(),
            response=mock_response
        )

        result = format_api_error(http_error)

        assert isinstance(result, YNABAPIError)
        assert result.status_code == 500
        assert "server error" in result.message.lower()

    def test_format_timeout_error(self):
        """Should convert TimeoutException to YNABNetworkError."""
        timeout_error = httpx.TimeoutException("Request timed out", request=Mock())

        result = format_api_error(timeout_error)

        assert isinstance(result, YNABNetworkError)
        assert "timed out" in result.message.lower() or "timeout" in result.message.lower()
        assert result.original_error is timeout_error

    def test_format_connect_error(self):
        """Should convert ConnectError to YNABNetworkError."""
        connect_error = httpx.ConnectError("Connection refused")

        result = format_api_error(connect_error)

        assert isinstance(result, YNABNetworkError)
        assert "connection" in result.message.lower()
        assert result.original_error is connect_error

    def test_format_request_error(self):
        """Should convert generic RequestError to YNABNetworkError."""
        request_error = httpx.RequestError("Network error")

        result = format_api_error(request_error)

        assert isinstance(result, YNABNetworkError)
        assert "network" in result.message.lower()
        assert result.original_error is request_error

    def test_format_value_error(self):
        """Should convert ValueError to YNABAPIError."""
        value_error = ValueError("Invalid JSON")

        result = format_api_error(value_error)

        assert isinstance(result, YNABAPIError)
        assert "invalid" in result.message.lower() or "error" in result.message.lower()

    def test_format_generic_exception(self):
        """Should convert generic Exception to YNABAPIError."""
        generic_error = Exception("Something went wrong")

        result = format_api_error(generic_error)

        assert isinstance(result, YNABAPIError)
        assert "Something went wrong" in result.message
