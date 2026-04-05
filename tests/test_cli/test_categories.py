"""Tests for categories CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ynab_cli.cli.main import app


@pytest.fixture
def mock_budget_category_response():
    """Mock response from YNAB API for category month update."""
    return {
        "data": {
            "category": {
                "id": "cat-1",
                "name": "Rent/Mortgage",
                "budgeted": 250000,  # $250.00
                "activity": -100000,
                "balance": 150000,
                "hidden": False,
                "deleted": False,
                "goal_type": None,
                "goal_target": None,
                "note": None,
            }
        }
    }


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


class TestCategoriesBudget:
    """Tests for 'ynab categories budget' command."""

    def test_budget_requires_api_token(self, cli_runner, clean_env):
        """Test that categories budget fails without API token configured."""
        with patch("ynab_cli.cli.categories.settings", None):
            result = cli_runner.invoke(
                app, ["categories", "budget", "cat-1", "--month", "2026-04-01", "--amount", "250"]
            )
            assert result.exit_code != 0
            assert (
                "API token not configured" in result.stdout
                or "API token is required" in result.stdout
            )

    def test_budget_basic_json_output(self, cli_runner, mock_budget_category_response):
        """Test basic categories budget command returns JSON with updated category."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_category_month = AsyncMock(
                    return_value=mock_budget_category_response
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "categories",
                        "budget",
                        "cat-1",
                        "--month",
                        "2026-04-01",
                        "--amount",
                        "250.00",
                    ],
                )

                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                assert "category" in output_data
                assert output_data["category"]["name"] == "Rent/Mortgage"
                # Verify milliunit conversion: 250000 -> 250.0
                assert output_data["category"]["budgeted"] == 250.0

                # Verify API called with correct args (amount in milliunits)
                mock_client.update_category_month.assert_called_once_with(
                    category_id="cat-1",
                    month="2026-04-01",
                    budget_id=None,
                    budgeted=250000,
                )

    def test_budget_table_output(self, cli_runner, mock_budget_category_response):
        """Test categories budget with --table flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_category_month = AsyncMock(
                    return_value=mock_budget_category_response
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "categories",
                        "budget",
                        "cat-1",
                        "--month",
                        "2026-04-01",
                        "--amount",
                        "250.00",
                        "--table",
                    ],
                )

                assert result.exit_code == 0
                assert "Category budget updated successfully" in result.stdout
                assert "Rent/Mortgage" in result.stdout

    def test_budget_with_budget_override(self, cli_runner, mock_budget_category_response):
        """Test categories budget with --budget flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_category_month = AsyncMock(
                    return_value=mock_budget_category_response
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "categories",
                        "budget",
                        "cat-1",
                        "--month",
                        "2026-04-01",
                        "--amount",
                        "100",
                        "--budget",
                        "budget-2",
                    ],
                )

                assert result.exit_code == 0
                mock_client.update_category_month.assert_called_once_with(
                    category_id="cat-1",
                    month="2026-04-01",
                    budget_id="budget-2",
                    budgeted=100000,
                )

    def test_budget_zero_amount(self, cli_runner, mock_budget_category_response):
        """Test assigning $0 to clear a category's budget."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        # Adjust mock to reflect zero budget
        mock_budget_category_response["data"]["category"]["budgeted"] = 0
        mock_budget_category_response["data"]["category"]["balance"] = -100000

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_category_month = AsyncMock(
                    return_value=mock_budget_category_response
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "categories",
                        "budget",
                        "cat-1",
                        "--month",
                        "2026-04-01",
                        "--amount",
                        "0",
                    ],
                )

                assert result.exit_code == 0
                mock_client.update_category_month.assert_called_once_with(
                    category_id="cat-1",
                    month="2026-04-01",
                    budget_id=None,
                    budgeted=0,
                )

    def test_budget_api_error(self, cli_runner):
        """Test categories budget handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            with patch("ynab_cli.cli.categories.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_category_month = AsyncMock(
                    side_effect=Exception("API connection failed")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "categories",
                        "budget",
                        "cat-1",
                        "--month",
                        "2026-04-01",
                        "--amount",
                        "250",
                    ],
                )

                assert result.exit_code != 0
                assert "Error" in result.stdout


class TestGetCategory:
    """Tests for categories get command."""

    @pytest.fixture
    def cli_runner(self):
        from typer.testing import CliRunner
        return CliRunner()

    @pytest.fixture
    def mock_settings(self):
        s = MagicMock()
        s.api_token = "test-token"
        s.budget_id = "budget-1"
        return s

    def test_get_category_json_output(self, cli_runner, mock_settings):
        """Fetch a single category by ID, JSON output."""
        mock_response = {
            "data": {
                "category": {
                    "id": "cat-abc",
                    "name": "Groceries",
                    "budgeted": 300000,
                    "activity": -125000,
                    "balance": 175000,
                    "goal_type": "NEED",
                    "goal_target": 300000,
                    "hidden": False,
                    "deleted": False,
                }
            }
        }

        with (
            patch("ynab_cli.cli.categories.settings", mock_settings),
            patch("ynab_cli.cli.categories.YNABClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.get_category = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = cli_runner.invoke(
                app,
                ["categories", "get", "cat-abc"],
            )

            assert result.exit_code == 0
            output = json.loads(result.stdout)
            assert output["category"]["id"] == "cat-abc"
            assert output["category"]["budgeted"] == 300.0
            assert output["category"]["balance"] == 175.0
            assert output["category"]["goal_type_name"] == "Plan Your Spending"
            mock_client.get_category.assert_called_once_with(
                category_id="cat-abc", budget_id=None
            )

    def test_get_category_with_month(self, cli_runner, mock_settings):
        """Fetch a category for a specific month."""
        mock_response = {
            "data": {
                "category": {
                    "id": "cat-abc",
                    "name": "Groceries",
                    "budgeted": 300000,
                    "activity": -125000,
                    "balance": 175000,
                    "goal_type": None,
                }
            }
        }

        with (
            patch("ynab_cli.cli.categories.settings", mock_settings),
            patch("ynab_cli.cli.categories.YNABClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.get_category_month = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = cli_runner.invoke(
                app,
                ["categories", "get", "cat-abc", "--month", "2026-04-01"],
            )

            assert result.exit_code == 0
            output = json.loads(result.stdout)
            assert output["category"]["id"] == "cat-abc"
            mock_client.get_category_month.assert_called_once_with(
                category_id="cat-abc", month="2026-04-01", budget_id=None
            )

    def test_get_category_no_token(self, cli_runner):
        """Error when API token not configured."""
        mock_settings = MagicMock()
        mock_settings.api_token = None

        with patch("ynab_cli.cli.categories.settings", mock_settings):
            result = cli_runner.invoke(app, ["categories", "get", "cat-abc"])
            assert result.exit_code != 0
