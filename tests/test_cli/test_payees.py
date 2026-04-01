"""Tests for payees CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ynab_cli.cli.main import app


@pytest.fixture
def mock_payees_response():
    """Mock response from YNAB API for payees list."""
    return {
        "data": {
            "payees": [
                {
                    "id": "payee-1",
                    "name": "Amazon",
                    "deleted": False,
                    "transfer_account_id": None,
                },
                {
                    "id": "payee-2",
                    "name": "Venmo",
                    "deleted": False,
                    "transfer_account_id": None,
                },
                {
                    "id": "payee-3",
                    "name": "Walmart",
                    "deleted": False,
                    "transfer_account_id": None,
                },
                {
                    "id": "payee-4",
                    "name": "Amazon Prime",
                    "deleted": False,
                    "transfer_account_id": None,
                },
                {
                    "id": "payee-5",
                    "name": "Deleted Payee",
                    "deleted": True,
                    "transfer_account_id": None,
                },
            ],
            "server_knowledge": 123,
        }
    }


class TestPayeesList:
    """Tests for 'ynab payees list' command."""

    def test_payees_list_requires_api_token(self, cli_runner, clean_env):
        """Test that payees list fails without API token configured."""
        with patch("ynab_cli.cli.payees.settings", None):
            result = cli_runner.invoke(app, ["payees", "list"])
            assert result.exit_code != 0
            assert (
                "API token not configured" in result.stdout
                or "API token is required" in result.stdout
            )

    def test_payees_list_basic(self, cli_runner, mock_payees_response):
        """Test basic payees list command (default JSON output)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list"])

                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                assert "payees" in output_data
                assert len(output_data["payees"]) == 5
                mock_client.get_payees.assert_called_once_with(budget_id=None)

    def test_payees_list_search(self, cli_runner, mock_payees_response):
        """Test payees list with --search filter."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list", "--search", "Amazon"])

                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                assert len(output_data["payees"]) == 2
                names = [p["name"] for p in output_data["payees"]]
                assert "Amazon" in names
                assert "Amazon Prime" in names

    def test_payees_list_search_case_insensitive(self, cli_runner, mock_payees_response):
        """Test that --search is case-insensitive."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list", "--search", "venmo"])

                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                assert len(output_data["payees"]) == 1
                assert output_data["payees"][0]["name"] == "Venmo"

    def test_payees_list_search_no_results(self, cli_runner, mock_payees_response):
        """Test --search with no matches returns empty list."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list", "--search", "NonExistent"])

                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                assert len(output_data["payees"]) == 0

    def test_payees_list_table_output(self, cli_runner, mock_payees_response):
        """Test payees list with table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list", "--table"])

                assert result.exit_code == 0
                assert "Amazon" in result.stdout
                assert "Venmo" in result.stdout

    def test_payees_list_table_with_search(self, cli_runner, mock_payees_response):
        """Test table output includes search term in title."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list", "--search", "Amazon", "--table"])

                assert result.exit_code == 0
                assert "Amazon" in result.stdout

    def test_payees_list_with_budget_override(self, cli_runner, mock_payees_response):
        """Test payees list with --budget flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list", "--budget", "budget-2"])

                assert result.exit_code == 0
                mock_client.get_payees.assert_called_once_with(budget_id="budget-2")

    def test_payees_list_api_error(self, cli_runner):
        """Test payees list handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.payees.settings", mock_settings):
            with patch("ynab_cli.cli.payees.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_payees = AsyncMock(side_effect=Exception("API connection failed"))
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["payees", "list"])

                assert result.exit_code != 0
                assert "Error" in result.stdout
