"""Tests for budgets CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from ynab_cli.cli.main import app


@pytest.fixture
def mock_budgets_response():
    """Mock response from YNAB API for budgets list."""
    return {
        "data": {
            "budgets": [
                {
                    "id": "budget-1",
                    "name": "My Budget",
                    "currency_format": {
                        "iso_code": "USD",
                        "example_format": "$123.45",
                        "decimal_digits": 2,
                        "decimal_separator": ".",
                        "symbol_first": True,
                        "group_separator": ",",
                        "currency_symbol": "$",
                        "display_symbol": True
                    }
                },
                {
                    "id": "budget-2",
                    "name": "Another Budget",
                    "currency_format": {
                        "iso_code": "EUR",
                        "example_format": "€123.45",
                        "decimal_digits": 2,
                        "decimal_separator": ".",
                        "symbol_first": True,
                        "group_separator": ",",
                        "currency_symbol": "€",
                        "display_symbol": True
                    }
                }
            ],
            "server_knowledge": 123
        }
    }


@pytest.fixture
def mock_budgets_with_accounts_response():
    """Mock response from YNAB API for budgets list with accounts."""
    return {
        "data": {
            "budgets": [
                {
                    "id": "budget-1",
                    "name": "My Budget",
                    "currency_format": {
                        "iso_code": "USD",
                        "example_format": "$123.45",
                        "decimal_digits": 2,
                        "decimal_separator": ".",
                        "symbol_first": True,
                        "group_separator": ",",
                        "currency_symbol": "$",
                        "display_symbol": True
                    },
                    "accounts": [
                        {"id": "acc-1", "name": "Checking"},
                        {"id": "acc-2", "name": "Savings"}
                    ]
                },
                {
                    "id": "budget-2",
                    "name": "Another Budget",
                    "currency_format": {
                        "iso_code": "EUR",
                        "example_format": "€123.45",
                        "decimal_digits": 2,
                        "decimal_separator": ".",
                        "symbol_first": True,
                        "group_separator": ",",
                        "currency_symbol": "€",
                        "display_symbol": True
                    },
                    "accounts": [
                        {"id": "acc-3", "name": "Credit Card"}
                    ]
                }
            ],
            "server_knowledge": 123
        }
    }


class TestBudgetsList:
    """Tests for 'ynab budgets list' command."""

    def test_budgets_list_requires_api_token(self, cli_runner, clean_env):
        """Test that budgets list fails without API token configured."""
        with patch("ynab_cli.cli.budgets.settings", None):
            result = cli_runner.invoke(app, ["budgets", "list"])
            assert result.exit_code != 0
            assert "API token not configured" in result.stdout or "API token is required" in result.stdout

    def test_budgets_list_basic(self, cli_runner, mock_budgets_response):
        """Test basic budgets list command."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.budgets.settings", mock_settings):
            with patch("ynab_cli.cli.budgets.YNABClient") as mock_client_class:
                # Setup mock client
                mock_client = AsyncMock()
                mock_client.get_budgets = AsyncMock(return_value=mock_budgets_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["budgets", "list"])

                assert result.exit_code == 0
                assert "My Budget" in result.stdout
                assert "Another Budget" in result.stdout
                assert "USD" in result.stdout
                assert "EUR" in result.stdout

                # Verify client was called correctly
                mock_client.get_budgets.assert_called_once_with(include_accounts=False)

    def test_budgets_list_json_output(self, cli_runner, mock_budgets_response):
        """Test budgets list with JSON output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.budgets.settings", mock_settings):
            with patch("ynab_cli.cli.budgets.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_budgets = AsyncMock(return_value=mock_budgets_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["budgets", "list", "--json"])

                assert result.exit_code == 0

                # Verify output is valid JSON
                output_data = json.loads(result.stdout)
                assert "budgets" in output_data
                assert len(output_data["budgets"]) == 2
                assert output_data["budgets"][0]["name"] == "My Budget"

    def test_budgets_list_with_accounts(self, cli_runner, mock_budgets_with_accounts_response):
        """Test budgets list with include-accounts flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.budgets.settings", mock_settings):
            with patch("ynab_cli.cli.budgets.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_budgets = AsyncMock(return_value=mock_budgets_with_accounts_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["budgets", "list", "--include-accounts"])

                assert result.exit_code == 0
                # Should show account count
                assert "2 accounts" in result.stdout or "Accounts: 2" in result.stdout
                assert "1 account" in result.stdout or "Accounts: 1" in result.stdout

                # Verify client was called with include_accounts=True
                mock_client.get_budgets.assert_called_once_with(include_accounts=True)

    def test_budgets_list_api_error(self, cli_runner):
        """Test budgets list handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.budgets.settings", mock_settings):
            with patch("ynab_cli.cli.budgets.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_budgets = AsyncMock(side_effect=Exception("API connection failed"))
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["budgets", "list"])

                assert result.exit_code != 0
                assert "Error" in result.stdout or "Failed" in result.stdout
