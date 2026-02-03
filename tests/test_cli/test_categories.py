"""Tests for categories CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ynab_cli.cli.main import app


@pytest.fixture
def mock_categories_response():
    """Mock response from YNAB API for categories list."""
    return {
        "data": {
            "category_groups": [
                {
                    "id": "group-1",
                    "name": "Monthly Bills",
                    "hidden": False,
                    "deleted": False,
                    "categories": [
                        {
                            "id": "cat-1",
                            "name": "Rent/Mortgage",
                            "hidden": False,
                            "deleted": False,
                            "budgeted": 1500000,  # $1,500.00
                            "activity": -1500000,
                            "balance": 0,
                            "goal_type": None,
                            "goal_target": None,
                        },
                        {
                            "id": "cat-2",
                            "name": "Electric",
                            "hidden": False,
                            "deleted": False,
                            "budgeted": 150000,  # $150.00
                            "activity": -120000,  # -$120.00
                            "balance": 30000,  # $30.00
                            "goal_type": "MF",  # Monthly Funding
                            "goal_target": 150000,
                        },
                    ],
                },
                {
                    "id": "group-2",
                    "name": "Savings Goals",
                    "hidden": False,
                    "deleted": False,
                    "categories": [
                        {
                            "id": "cat-3",
                            "name": "Emergency Fund",
                            "hidden": False,
                            "deleted": False,
                            "budgeted": 500000,  # $500.00
                            "activity": 0,
                            "balance": 5000000,  # $5,000.00
                            "goal_type": "TB",  # Target Balance
                            "goal_target": 10000000,  # $10,000.00
                        },
                        {
                            "id": "cat-4",
                            "name": "Vacation",
                            "hidden": False,
                            "deleted": False,
                            "budgeted": 200000,  # $200.00
                            "activity": 0,
                            "balance": 800000,  # $800.00
                            "goal_type": "TBD",  # Target by Date
                            "goal_target": 2000000,  # $2,000.00
                        },
                    ],
                },
            ],
            "server_knowledge": 789,
        }
    }


class TestCategoriesList:
    """Tests for 'ynab categories list' command."""

    def test_categories_list_requires_api_token(self, cli_runner, clean_env):
        """Test that categories list fails without API token configured."""
        with patch("ynab_cli.cli.categories.settings", None):
            result = cli_runner.invoke(app, ["categories", "list"])
            assert result.exit_code != 0
            assert (
                "API token not configured" in result.stdout
                or "API token is required" in result.stdout
            )

    def test_categories_list_basic(self, cli_runner, mock_categories_response):
        """Test basic categories list command (default JSON output)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list"])

                assert result.exit_code == 0

                # Verify output is valid JSON (default)
                output_data = json.loads(result.stdout)
                assert "category_groups" in output_data
                assert len(output_data["category_groups"]) == 2
                assert output_data["category_groups"][0]["name"] == "Monthly Bills"

                # Verify client was called correctly
                mock_client.get_categories.assert_called_once_with(budget_id=None)

    def test_categories_list_table_output(self, cli_runner, mock_categories_response):
        """Test categories list with table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list", "--table"])

                assert result.exit_code == 0

                # Check category group names
                assert "Monthly Bills" in result.stdout
                assert "Savings Goals" in result.stdout

                # Check category names
                assert "Rent/Mortgage" in result.stdout
                assert "Electric" in result.stdout

    def test_categories_list_with_budget_override(self, cli_runner, mock_categories_response):
        """Test categories list with --budget flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list", "--budget", "budget-2"])

                assert result.exit_code == 0
                # Verify client was called with overridden budget
                mock_client.get_categories.assert_called_once_with(budget_id="budget-2")

    def test_categories_list_with_goals(self, cli_runner, mock_categories_response):
        """Test categories list with --show-goals flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list", "--show-goals", "--table"])

                assert result.exit_code == 0
                # Should show goal types
                assert "MF" in result.stdout or "Monthly Funding" in result.stdout
                assert "TB" in result.stdout or "Target Balance" in result.stdout
                assert "TBD" in result.stdout or "Target by Date" in result.stdout

    def test_categories_list_shows_hierarchy(self, cli_runner, mock_categories_response):
        """Test that categories are grouped under their category groups."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list", "--table"])

                assert result.exit_code == 0
                # Groups should appear before their categories in output
                output = result.stdout
                monthly_bills_pos = output.find("Monthly Bills")
                rent_pos = output.find("Rent/Mortgage")
                savings_goals_pos = output.find("Savings Goals")
                emergency_pos = output.find("Emergency Fund")

                assert monthly_bills_pos < rent_pos
                assert savings_goals_pos < emergency_pos

    def test_categories_list_shows_budgeted_activity_balance(
        self, cli_runner, mock_categories_response
    ):
        """Test that budgeted, activity, and balance are all displayed."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list", "--table"])

                assert result.exit_code == 0
                # Should show column headers or labels for budgeted/activity/balance
                output_lower = result.stdout.lower()
                assert "budgeted" in output_lower or "budget" in output_lower
                assert "activity" in output_lower or "spent" in output_lower
                assert "balance" in output_lower or "available" in output_lower

    def test_categories_list_api_error(self, cli_runner):
        """Test categories list handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_categories = AsyncMock(
                    side_effect=Exception("API connection failed")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["categories", "list"])

                assert result.exit_code != 0
                assert "Error" in result.stdout or "Failed" in result.stdout
