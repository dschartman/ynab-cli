"""Tests for months CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from ynab_cli.cli.main import app


@pytest.fixture
def cli_runner():
    """Fixture providing a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_month_response():
    """Mock response from YNAB API for month details."""
    return {
        "data": {
            "month": {
                "month": "2024-01-01",
                "income": 500000,  # $500.00
                "budgeted": 450000,  # $450.00
                "activity": -380000,  # -$380.00
                "to_be_budgeted": 50000,  # $50.00
                "age_of_money": 45,
                "categories": [
                    {
                        "id": "cat-1",
                        "name": "Groceries",
                        "budgeted": 200000,  # $200.00
                        "activity": -150000,  # -$150.00
                        "balance": 50000,  # $50.00
                    },
                    {
                        "id": "cat-2",
                        "name": "Dining Out",
                        "budgeted": 100000,  # $100.00
                        "activity": -80000,  # -$80.00
                        "balance": 20000,  # $20.00
                    },
                    {
                        "id": "cat-3",
                        "name": "Gas",
                        "budgeted": 150000,  # $150.00
                        "activity": -150000,  # -$150.00
                        "balance": 0,
                    },
                ]
            }
        }
    }


class TestMonthsGet:
    """Tests for 'ynab months get' command."""

    def test_get_current_month(self, cli_runner, mock_month_response):
        """Test getting current month details."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get"])

                assert result.exit_code == 0
                # Should show month summary
                assert "2024-01" in result.stdout
                assert "$500.00" in result.stdout  # Income
                assert "$450.00" in result.stdout  # Budgeted
                assert "45" in result.stdout  # Age of money
                # Verify API was called with 'current'
                mock_client.get_month.assert_called_once()
                call_kwargs = mock_client.get_month.call_args[1]
                assert call_kwargs["month"] == "current"

    def test_get_specific_month(self, cli_runner, mock_month_response):
        """Test getting specific month by date."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get", "2024-01-01"])

                assert result.exit_code == 0
                # Verify API was called with the specified month
                mock_client.get_month.assert_called_once()
                call_kwargs = mock_client.get_month.call_args[1]
                assert call_kwargs["month"] == "2024-01-01"

    def test_get_month_json_output(self, cli_runner, mock_month_response):
        """Test months get with JSON output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get", "--json"])

                assert result.exit_code == 0
                # Should output valid JSON
                output = json.loads(result.stdout)
                assert output["month"]["month"] == "2024-01-01"
                assert output["month"]["income"] == 500000

    def test_get_month_shows_categories(self, cli_runner, mock_month_response):
        """Test that month output includes category breakdown."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get"])

                assert result.exit_code == 0
                # Should show category names and amounts
                assert "Groceries" in result.stdout
                assert "Dining Out" in result.stdout
                assert "Gas" in result.stdout
                # Should show category amounts in dollars
                assert "$200.00" in result.stdout  # Groceries budgeted
                assert "$100.00" in result.stdout  # Dining Out budgeted

    def test_get_month_requires_token(self, cli_runner):
        """Test months get requires API token."""
        mock_settings = MagicMock()
        mock_settings.api_token = None

        with patch("ynab_cli.cli.months.settings", mock_settings):
            result = cli_runner.invoke(app, ["months", "get"])

            assert result.exit_code != 0
            assert "token" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_get_month_with_budget_override(self, cli_runner, mock_month_response):
        """Test months get with budget ID override."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, [
                    "months", "get",
                    "--budget", "different-budget"
                ])

                assert result.exit_code == 0
                # Verify budget override was passed
                call_kwargs = mock_client.get_month.call_args[1]
                assert call_kwargs.get("budget_id") == "different-budget"

    def test_get_month_api_error(self, cli_runner):
        """Test months get handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(
                    side_effect=Exception("API Error: Invalid month")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get"])

                assert result.exit_code != 0
                assert "Error" in result.stdout or "error" in result.stdout

    def test_get_month_converts_milliunits(self, cli_runner, mock_month_response):
        """Test that month amounts are converted from milliunits to dollars."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get"])

                assert result.exit_code == 0
                # Check that milliunits were converted
                # 500000 milliunits = $500.00
                assert "$500.00" in result.stdout
                # -380000 milliunits = -$380.00
                assert "$380.00" in result.stdout or "-$380.00" in result.stdout

    def test_get_month_shows_to_be_budgeted(self, cli_runner, mock_month_response):
        """Test that month output shows To Be Budgeted amount."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.months.settings", mock_settings):
            with patch("ynab_cli.cli.months.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_month = AsyncMock(return_value=mock_month_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["months", "get"])

                assert result.exit_code == 0
                # Should show To Be Budgeted (50000 milliunits = $50.00)
                assert "To Be Budgeted" in result.stdout or "to be budgeted" in result.stdout.lower()
                assert "$50.00" in result.stdout
