"""Tests for logging configuration."""

import logging

from ynab_cli.logging_config import (
    get_logger,
    is_verbose,
    log_api_request,
    log_api_response,
    setup_logging,
)


class TestLoggingSetup:
    """Tests for logging setup."""

    def test_setup_logging_default(self):
        """setup_logging should configure logger at WARNING level by default."""
        setup_logging(verbose=False)
        logger = get_logger()

        assert logger.level == logging.WARNING
        assert is_verbose() is False

    def test_setup_logging_verbose(self):
        """setup_logging with verbose=True should set INFO level."""
        setup_logging(verbose=True)
        logger = get_logger()

        assert logger.level == logging.INFO
        assert is_verbose() is True

        # Clean up
        setup_logging(verbose=False)

    def test_get_logger_returns_configured_logger(self):
        """get_logger should return a configured logger."""
        logger = get_logger()

        assert logger is not None
        assert logger.name == "ynab_cli"
        assert len(logger.handlers) > 0

    def test_log_api_request_without_params(self):
        """log_api_request should execute without errors."""
        setup_logging(verbose=True)

        # Should not raise any exceptions
        log_api_request("GET", "https://api.ynab.com/v1/budgets")

        # Clean up
        setup_logging(verbose=False)

    def test_log_api_request_with_params(self):
        """log_api_request with params should execute without errors."""
        setup_logging(verbose=True)

        # Should not raise any exceptions
        log_api_request(
            "GET",
            "https://api.ynab.com/v1/budgets",
            params={"include_accounts": "true"}
        )

        # Clean up
        setup_logging(verbose=False)

    def test_log_api_response(self):
        """log_api_response should execute without errors."""
        setup_logging(verbose=True)

        # Should not raise any exceptions
        log_api_response(200, "https://api.ynab.com/v1/budgets", 123.4)

        # Clean up
        setup_logging(verbose=False)

    def test_verbose_flag_enables_info_logging(self):
        """verbose flag should enable INFO level logging."""
        setup_logging(verbose=False)
        logger = get_logger()
        assert not logger.isEnabledFor(logging.INFO)

        setup_logging(verbose=True)
        logger = get_logger()
        assert logger.isEnabledFor(logging.INFO)

        # Clean up
        setup_logging(verbose=False)
