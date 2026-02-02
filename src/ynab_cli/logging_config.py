"""Logging configuration for YNAB CLI."""

import logging
import sys
from typing import Optional


# Module-level logger
_logger: Optional[logging.Logger] = None
_verbose_enabled = False


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the CLI.

    Args:
        verbose: If True, enable verbose logging (INFO level)
    """
    global _logger, _verbose_enabled
    _verbose_enabled = verbose

    # Create logger
    _logger = logging.getLogger("ynab_cli")

    # Set level based on verbose flag
    if verbose:
        _logger.setLevel(logging.INFO)
    else:
        _logger.setLevel(logging.WARNING)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    _logger.addHandler(handler)

    # Prevent propagation to root logger
    _logger.propagate = False


def get_logger() -> logging.Logger:
    """
    Get the CLI logger.

    Returns:
        The configured logger instance
    """
    global _logger
    if _logger is None:
        setup_logging()
    return _logger


def is_verbose() -> bool:
    """
    Check if verbose mode is enabled.

    Returns:
        True if verbose mode is enabled
    """
    return _verbose_enabled


def log_api_request(method: str, url: str, params: Optional[dict] = None) -> None:
    """
    Log an API request.

    Args:
        method: HTTP method
        url: Request URL
        params: Optional query parameters
    """
    logger = get_logger()
    if params:
        logger.info(f"API Request: {method} {url} params={params}")
    else:
        logger.info(f"API Request: {method} {url}")


def log_api_response(status_code: int, url: str, duration_ms: float) -> None:
    """
    Log an API response.

    Args:
        status_code: HTTP status code
        url: Request URL
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger()
    logger.info(f"API Response: {status_code} {url} ({duration_ms:.1f}ms)")
