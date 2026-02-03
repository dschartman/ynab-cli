"""Tests for accounts CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ynab_cli.cli.main import app


@pytest.fixture
def mock_accounts_response():
    """Mock response from YNAB API for accounts list."""
    return {
        "data": {
            "accounts": [
                {
                    "id": "acc-1",
                    "name": "Checking Account",
                    "type": "checking",
                    "on_budget": True,
                    "closed": False,
                    "balance": 123450,  # $123.45 in milliunits
                    "cleared_balance": 100000,  # $100.00
                    "uncleared_balance": 23450,  # $23.45
                },
                {
                    "id": "acc-2",
                    "name": "Savings Account",
                    "type": "savings",
                    "on_budget": True,
                    "closed": False,
                    "balance": 5000000,  # $5,000.00
                    "cleared_balance": 5000000,
                    "uncleared_balance": 0,
                },
                {
                    "id": "acc-3",
                    "name": "Credit Card",
                    "type": "creditCard",
                    "on_budget": True,
                    "closed": False,
                    "balance": -50000,  # -$50.00
                    "cleared_balance": -50000,
                    "uncleared_balance": 0,
                },
                {
                    "id": "acc-4",
                    "name": "Old Account",
                    "type": "checking",
                    "on_budget": True,
                    "closed": True,
                    "balance": 0,
                    "cleared_balance": 0,
                    "uncleared_balance": 0,
                },
            ],
            "server_knowledge": 123,
        }
    }


class TestAccountsList:
    """Tests for 'ynab accounts list' command."""

    def test_accounts_list_requires_api_token(self, cli_runner, clean_env):
        """Test that accounts list fails without API token configured."""
        with patch("ynab_cli.cli.accounts.settings", None):
            result = cli_runner.invoke(app, ["accounts", "list"])
            assert result.exit_code != 0
            assert (
                "API token not configured" in result.stdout
                or "API token is required" in result.stdout
            )

    def test_accounts_list_basic(self, cli_runner, mock_accounts_response):
        """Test basic accounts list command (default JSON output)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.accounts.settings", mock_settings):
            with patch("ynab_cli.cli.accounts.YNABClient") as mock_client_class:
                # Setup mock client
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["accounts", "list"])

                assert result.exit_code == 0

                # Verify output is valid JSON (default)
                output_data = json.loads(result.stdout)
                assert "accounts" in output_data
                assert len(output_data["accounts"]) == 4
                assert output_data["accounts"][0]["name"] == "Checking Account"

                # Verify client was called with default budget
                mock_client.get_accounts.assert_called_once_with(budget_id=None)

    def test_accounts_list_table_output(self, cli_runner, mock_accounts_response):
        """Test accounts list with table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.accounts.settings", mock_settings):
            with patch("ynab_cli.cli.accounts.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["accounts", "list", "--table"])

                assert result.exit_code == 0

                # Check account names
                assert "Checking Account" in result.stdout
                assert "Savings Account" in result.stdout
                assert "Credit Card" in result.stdout

                # Check formatted balances (milliunits converted to dollars)
                assert "123.45" in result.stdout
                assert "5000.00" in result.stdout or "5,000.00" in result.stdout
                assert "-50.00" in result.stdout

    def test_accounts_list_with_budget_override(self, cli_runner, mock_accounts_response):
        """Test accounts list with --budget flag to override default."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.accounts.settings", mock_settings):
            with patch("ynab_cli.cli.accounts.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["accounts", "list", "--budget", "budget-2"])

                assert result.exit_code == 0
                # Verify client was called with overridden budget
                mock_client.get_accounts.assert_called_once_with(budget_id="budget-2")

    def test_accounts_list_shows_closed_status(self, cli_runner, mock_accounts_response):
        """Test that closed accounts are indicated in table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.accounts.settings", mock_settings):
            with patch("ynab_cli.cli.accounts.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["accounts", "list", "--table"])

                assert result.exit_code == 0
                # Should show closed indicator for Old Account
                assert "Old Account" in result.stdout
                # Look for closed indicator - could be "✓" or "Yes" or "Closed" etc.
                assert (
                    "closed" in result.stdout.lower()
                    or "✓" in result.stdout
                    or "yes" in result.stdout.lower()
                )

    def test_accounts_list_api_error(self, cli_runner):
        """Test accounts list handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.accounts.settings", mock_settings):
            with patch("ynab_cli.cli.accounts.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(side_effect=Exception("API connection failed"))
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["accounts", "list"])

                assert result.exit_code != 0
                assert "Error" in result.stdout or "Failed" in result.stdout


class TestMilliunitsConversion:
    """Tests for milliunit conversion helper."""

    def test_milliunits_to_dollars_positive(self):
        """Test converting positive milliunits to dollars."""
        from ynab_cli.cli.accounts import milliunits_to_dollars

        assert milliunits_to_dollars(1000) == 1.0
        assert milliunits_to_dollars(123450) == 123.45
        assert milliunits_to_dollars(5000000) == 5000.0

    def test_milliunits_to_dollars_negative(self):
        """Test converting negative milliunits to dollars."""
        from ynab_cli.cli.accounts import milliunits_to_dollars

        assert milliunits_to_dollars(-1000) == -1.0
        assert milliunits_to_dollars(-50000) == -50.0
        assert milliunits_to_dollars(-123450) == -123.45

    def test_milliunits_to_dollars_zero(self):
        """Test converting zero milliunits."""
        from ynab_cli.cli.accounts import milliunits_to_dollars

        assert milliunits_to_dollars(0) == 0.0

    def test_milliunits_to_dollars_precision(self):
        """Test that conversion maintains precision."""
        from ynab_cli.cli.accounts import milliunits_to_dollars

        # Edge case: ensure we don't lose precision
        assert milliunits_to_dollars(1) == 0.001
        assert milliunits_to_dollars(999) == 0.999
