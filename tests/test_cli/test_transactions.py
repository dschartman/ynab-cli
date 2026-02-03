"""Tests for transactions CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ynab_cli.cli.main import app


@pytest.fixture
def mock_transactions_response():
    """Mock response from YNAB API for transactions list."""
    return {
        "data": {
            "transactions": [
                {
                    "id": "txn-1",
                    "date": "2024-01-15",
                    "amount": -45000,  # -$45.00 (expense)
                    "memo": "Grocery shopping",
                    "cleared": "cleared",
                    "approved": True,
                    "payee_name": "Whole Foods",
                    "category_name": "Groceries",
                    "account_name": "Checking",
                },
                {
                    "id": "txn-2",
                    "date": "2024-01-14",
                    "amount": -12000,  # -$12.00
                    "memo": "Coffee",
                    "cleared": "cleared",
                    "approved": True,
                    "payee_name": "Starbucks",
                    "category_name": "Dining Out",
                    "account_name": "Credit Card",
                },
                {
                    "id": "txn-3",
                    "date": "2024-01-13",
                    "amount": 250000,  # $250.00 (income)
                    "memo": "Paycheck",
                    "cleared": "cleared",
                    "approved": True,
                    "payee_name": "Employer",
                    "category_name": "Income",
                    "account_name": "Checking",
                },
                {
                    "id": "txn-4",
                    "date": "2024-01-12",
                    "amount": -5000,  # -$5.00
                    "memo": None,
                    "cleared": "uncleared",
                    "approved": False,
                    "payee_name": "Gas Station",
                    "category_name": None,  # Uncategorized
                    "account_name": "Credit Card",
                },
            ],
            "server_knowledge": 456,
        }
    }


class TestTransactionsList:
    """Tests for 'ynab transactions list' command."""

    def test_transactions_list_requires_api_token(self, cli_runner, clean_env):
        """Test that transactions list fails without API token configured."""
        with patch("ynab_cli.cli.transactions.settings", None):
            result = cli_runner.invoke(app, ["transactions", "list"])
            assert result.exit_code != 0
            assert (
                "API token not configured" in result.stdout
                or "API token is required" in result.stdout
            )

    def test_transactions_list_basic(self, cli_runner, mock_transactions_response):
        """Test basic transactions list command with JSON output (default)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list"])

                assert result.exit_code == 0
                # Verify output is valid JSON
                output_data = json.loads(result.stdout)
                assert "transactions" in output_data
                assert len(output_data["transactions"]) == 4
                assert output_data["transactions"][0]["payee_name"] == "Whole Foods"
                assert output_data["transactions"][1]["payee_name"] == "Starbucks"
                assert output_data["transactions"][2]["payee_name"] == "Employer"

                # Verify client was called correctly
                mock_client.get_transactions.assert_called_once()

    def test_transactions_list_table_output(self, cli_runner, mock_transactions_response):
        """Test transactions list with table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list", "--table"])

                assert result.exit_code == 0

                # Check transaction data appears in table format
                assert "Whole Foods" in result.stdout
                assert "Starbucks" in result.stdout
                assert "Employer" in result.stdout

                # Check amounts are formatted as dollars
                assert "45.00" in result.stdout  # Expense
                assert "250.00" in result.stdout  # Income

    def test_transactions_list_with_since_date(self, cli_runner, mock_transactions_response):
        """Test transactions list with since_date filter."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app, ["transactions", "list", "--since-date", "2024-01-01"]
                )

                assert result.exit_code == 0
                # Verify client was called with since_date parameter
                call_kwargs = mock_client.get_transactions.call_args[1]
                assert call_kwargs.get("since_date") == "2024-01-01"

    def test_transactions_list_with_type_filter(self, cli_runner, mock_transactions_response):
        """Test transactions list with type filter (unapproved/uncategorized)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list", "--type", "unapproved"])

                assert result.exit_code == 0
                # Verify client was called with transaction_type parameter
                call_kwargs = mock_client.get_transactions.call_args[1]
                assert call_kwargs.get("transaction_type") == "unapproved"

    def test_transactions_list_with_limit(self, cli_runner, mock_transactions_response):
        """Test transactions list with limit."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list", "--limit", "2"])

                assert result.exit_code == 0
                # Should only show 2 transactions in table output
                # We can't easily count rows in the table, but at least verify success
                # JSON test below is more specific

    def test_transactions_list_with_limit_table(self, cli_runner, mock_transactions_response):
        """Test transactions list with limit and table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list", "--limit", "2", "--table"])

                assert result.exit_code == 0
                # Should only show 2 transactions in table output
                # We can't easily count rows in the table, but at least verify success
                assert result.stdout  # Output exists

    def test_transactions_list_with_budget_override(self, cli_runner, mock_transactions_response):
        """Test transactions list with --budget flag."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list", "--budget", "budget-2"])

                assert result.exit_code == 0
                # Verify client was called with overridden budget
                call_kwargs = mock_client.get_transactions.call_args[1]
                assert call_kwargs.get("budget_id") == "budget-2"

    def test_transactions_list_shows_cleared_status(self, cli_runner, mock_transactions_response):
        """Test that cleared/uncleared status is shown in table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(return_value=mock_transactions_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list", "--table"])

                assert result.exit_code == 0
                # Should show cleared status in table
                assert "cleared" in result.stdout.lower() or "uncleared" in result.stdout.lower()

    def test_transactions_list_api_error(self, cli_runner):
        """Test transactions list handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.default_budget_id = "budget-1"
        mock_settings.base_url = "https://api.ynab.com/v1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_transactions = AsyncMock(
                    side_effect=Exception("API connection failed")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "list"])

                assert result.exit_code != 0
                assert "Error" in result.stdout or "Failed" in result.stdout


class TestTransactionsCreate:
    """Tests for 'ynab transactions create' command."""

    def test_create_basic_transaction(self, cli_runner):
        """Test creating a basic transaction with required fields (JSON output by default)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "new-txn-123",
                    "date": "2024-01-15",
                    "amount": -12450,
                    "account_id": "acct-1",
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "create",
                        "--account",
                        "acct-1",
                        "--date",
                        "2024-01-15",
                        "--amount",
                        "-12.45",
                    ],
                )

                assert result.exit_code == 0
                # Verify JSON output
                output = json.loads(result.stdout)
                assert output["transaction"]["id"] == "new-txn-123"
                assert output["transaction"]["amount"] == -12.45
                # Verify API was called with milliunits
                call_args = mock_client.create_transaction.call_args
                assert call_args[1]["transaction"]["amount"] == -12450

    def test_create_transaction_with_all_fields(self, cli_runner):
        """Test creating transaction with all optional fields (JSON output by default)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "new-txn-456",
                    "date": "2024-01-20",
                    "amount": -5000,
                    "payee_name": "Coffee Shop",
                    "category_name": "Dining Out",
                    "memo": "Morning coffee",
                    "cleared": "cleared",
                    "approved": True,
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "create",
                        "--account",
                        "acct-1",
                        "--date",
                        "2024-01-20",
                        "--amount",
                        "-5.00",
                        "--payee",
                        "payee-1",
                        "--category",
                        "cat-1",
                        "--memo",
                        "Morning coffee",
                        "--cleared",
                        "--approved",
                    ],
                )

                assert result.exit_code == 0
                # Verify JSON output
                output = json.loads(result.stdout)
                assert output["transaction"]["id"] == "new-txn-456"
                assert output["transaction"]["memo"] == "Morning coffee"
                # Verify all fields were passed
                call_args = mock_client.create_transaction.call_args
                txn = call_args[1]["transaction"]
                assert txn["amount"] == -5000
                assert txn["payee_id"] == "payee-1"
                assert txn["category_id"] == "cat-1"
                assert txn["memo"] == "Morning coffee"
                assert txn["cleared"] == "cleared"
                assert txn["approved"] is True

    def test_create_transaction_table_output(self, cli_runner):
        """Test create command with table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "new-txn-789",
                    "date": "2024-01-25",
                    "amount": -25000,
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "create",
                        "--account",
                        "acct-1",
                        "--date",
                        "2024-01-25",
                        "--amount",
                        "-25.00",
                        "--table",
                    ],
                )

                assert result.exit_code == 0
                # Should show success message in table format
                assert "created" in result.stdout.lower() or "success" in result.stdout.lower()

    def test_create_transaction_requires_token(self, cli_runner):
        """Test create command fails without API token."""
        mock_settings = MagicMock()
        mock_settings.api_token = None

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            result = cli_runner.invoke(
                app,
                [
                    "transactions",
                    "create",
                    "--account",
                    "acct-1",
                    "--date",
                    "2024-01-15",
                    "--amount",
                    "-10.00",
                ],
            )

            assert result.exit_code != 0
            assert "token" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_create_transaction_milliunits_conversion(self, cli_runner):
        """Test amount conversion from dollars to milliunits."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "txn-1",
                    "date": "2024-01-15",
                    "amount": -12450,
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                # Test various amounts
                test_cases = [
                    ("1.00", 1000),
                    ("-12.45", -12450),
                    ("100.99", 100990),
                    ("-0.50", -500),
                ]

                for amount_str, expected_milliunits in test_cases:
                    result = cli_runner.invoke(
                        app,
                        [
                            "transactions",
                            "create",
                            "--account",
                            "acct-1",
                            "--date",
                            "2024-01-15",
                            "--amount",
                            amount_str,
                        ],
                    )

                    assert result.exit_code == 0
                    call_args = mock_client.create_transaction.call_args
                    assert call_args[1]["transaction"]["amount"] == expected_milliunits

    def test_create_transaction_api_error(self, cli_runner):
        """Test create command handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_transaction = AsyncMock(
                    side_effect=Exception("API Error: Invalid account")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "create",
                        "--account",
                        "invalid-account",
                        "--date",
                        "2024-01-15",
                        "--amount",
                        "-10.00",
                    ],
                )

                assert result.exit_code != 0
                assert "Error" in result.stdout or "error" in result.stdout

    def test_create_positive_amount_income(self, cli_runner):
        """Test creating transaction with positive amount (income) - JSON output by default."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "income-txn",
                    "date": "2024-01-15",
                    "amount": 100000,
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "create",
                        "--account",
                        "acct-1",
                        "--date",
                        "2024-01-15",
                        "--amount",
                        "100.00",  # Positive = income
                    ],
                )

                assert result.exit_code == 0
                # Verify JSON output
                output = json.loads(result.stdout)
                assert output["transaction"]["id"] == "income-txn"
                assert output["transaction"]["amount"] == 100.0
                # Verify API call
                call_args = mock_client.create_transaction.call_args
                assert call_args[1]["transaction"]["amount"] == 100000


class TestDollarsToMilliunits:
    """Tests for dollars_to_milliunits helper function."""

    def test_positive_amount(self):
        """Test converting positive dollar amount."""
        from ynab_cli.cli.transactions import dollars_to_milliunits

        assert dollars_to_milliunits(1.00) == 1000
        assert dollars_to_milliunits(10.50) == 10500
        assert dollars_to_milliunits(100.99) == 100990

    def test_negative_amount(self):
        """Test converting negative dollar amount."""
        from ynab_cli.cli.transactions import dollars_to_milliunits

        assert dollars_to_milliunits(-1.00) == -1000
        assert dollars_to_milliunits(-12.45) == -12450
        assert dollars_to_milliunits(-999.99) == -999990

    def test_zero_amount(self):
        """Test converting zero."""
        from ynab_cli.cli.transactions import dollars_to_milliunits

        assert dollars_to_milliunits(0.00) == 0

    def test_small_amount(self):
        """Test converting small amounts."""
        from ynab_cli.cli.transactions import dollars_to_milliunits

        assert dollars_to_milliunits(0.01) == 10
        assert dollars_to_milliunits(0.50) == 500
        assert dollars_to_milliunits(-0.99) == -990


class TestTransactionsUpdate:
    """Tests for 'ynab transactions update' command."""

    def test_update_transaction_amount(self, cli_runner):
        """Test updating transaction amount with JSON output (default)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "txn-123",
                    "date": "2024-01-15",
                    "amount": -20000,  # Updated to -$20.00
                    "account_id": "acct-1",
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app, ["transactions", "update", "txn-123", "--amount", "-20.00"]
                )

                assert result.exit_code == 0
                # Verify JSON output
                output = json.loads(result.stdout)
                assert output["transaction"]["id"] == "txn-123"
                assert output["transaction"]["amount"] == -20.0
                # Verify amount was converted to milliunits
                call_kwargs = mock_client.update_transaction.call_args[1]
                assert call_kwargs["amount"] == -20000

    def test_update_transaction_multiple_fields(self, cli_runner):
        """Test updating multiple transaction fields with JSON output (default)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "txn-456",
                    "amount": -15000,
                    "memo": "Updated memo",
                    "cleared": "cleared",
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "update",
                        "txn-456",
                        "--amount",
                        "-15.00",
                        "--memo",
                        "Updated memo",
                        "--cleared",
                    ],
                )

                assert result.exit_code == 0
                # Verify JSON output
                output = json.loads(result.stdout)
                assert output["transaction"]["id"] == "txn-456"
                assert output["transaction"]["amount"] == -15.0
                assert output["transaction"]["memo"] == "Updated memo"
                # Verify API was called correctly
                call_kwargs = mock_client.update_transaction.call_args[1]
                assert call_kwargs["amount"] == -15000
                assert call_kwargs["memo"] == "Updated memo"
                assert call_kwargs["cleared"] == "cleared"

    def test_update_transaction_requires_token(self, cli_runner):
        """Test update requires API token."""
        mock_settings = MagicMock()
        mock_settings.api_token = None

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            result = cli_runner.invoke(
                app, ["transactions", "update", "txn-123", "--amount", "-10.00"]
            )

            assert result.exit_code != 0
            assert "token" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_update_transaction_table_output(self, cli_runner):
        """Test update with table output."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {
            "data": {
                "transaction": {
                    "id": "txn-789",
                    "amount": -25000,
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app, ["transactions", "update", "txn-789", "--amount", "-25.00", "--table"]
                )

                assert result.exit_code == 0
                # Should show success message in table format
                assert "updated" in result.stdout.lower() or "success" in result.stdout.lower()

    def test_update_transaction_api_error(self, cli_runner):
        """Test update handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.update_transaction = AsyncMock(
                    side_effect=Exception("Transaction not found")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app, ["transactions", "update", "invalid-txn", "--amount", "-10.00"]
                )

                assert result.exit_code != 0
                assert "Error" in result.stdout or "error" in result.stdout


class TestTransactionsDelete:
    """Tests for 'ynab transactions delete' command."""

    def test_delete_transaction_with_confirm(self, cli_runner):
        """Test deleting transaction with --confirm flag (table output)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_response = {"data": {"transaction": {"id": "txn-123", "deleted": True}}}

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.delete_transaction = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(app, ["transactions", "delete", "txn-123", "--confirm"])

                assert result.exit_code == 0
                # Delete command outputs table format (no --table flag available yet)
                assert "deleted" in result.stdout.lower() or "success" in result.stdout.lower()
                assert "txn-123" in result.stdout
                mock_client.delete_transaction.assert_called_once()

    def test_delete_transaction_requires_token(self, cli_runner):
        """Test delete requires API token."""
        mock_settings = MagicMock()
        mock_settings.api_token = None

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            result = cli_runner.invoke(app, ["transactions", "delete", "txn-123", "--confirm"])

            assert result.exit_code != 0
            assert "token" in result.stdout.lower() or "login" in result.stdout.lower()

    def test_delete_transaction_api_error(self, cli_runner):
        """Test delete handles API errors gracefully."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.delete_transaction = AsyncMock(
                    side_effect=Exception("Transaction not found")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app, ["transactions", "delete", "invalid-txn", "--confirm"]
                )

                assert result.exit_code != 0
                assert "Error" in result.stdout or "error" in result.stdout


class TestTransactionsTransfer:
    """Tests for 'ynab transactions transfer' command."""

    def test_transfer_between_accounts(self, cli_runner):
        """Test creating a transfer between two accounts (table output)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        # Mock accounts response
        mock_accounts = {
            "data": {
                "accounts": [
                    {
                        "id": "acct-checking",
                        "name": "Checking",
                        "transfer_payee_id": "payee-checking",
                    },
                    {"id": "acct-savings", "name": "Savings", "transfer_payee_id": "payee-savings"},
                ]
            }
        }

        # Mock transaction creation response
        mock_txn_response = {
            "data": {
                "transaction": {
                    "id": "txn-transfer-123",
                    "amount": -100000,
                    "payee_id": "payee-savings",
                }
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts)
                mock_client.create_transaction = AsyncMock(return_value=mock_txn_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "transfer",
                        "--from-account",
                        "Checking",
                        "--to-account",
                        "Savings",
                        "--amount",
                        "100.00",
                        "--date",
                        "2024-01-15",
                    ],
                )

                assert result.exit_code == 0
                # Transfer command outputs table format (no --table flag available yet)
                assert "transfer" in result.stdout.lower()
                assert "txn-transfer-123" in result.stdout
                # Verify transaction was created with correct payee_id
                call_kwargs = mock_client.create_transaction.call_args[1]
                txn = call_kwargs["transaction"]
                assert txn["payee_id"] == "payee-savings"
                assert txn["amount"] == -100000  # Negative (leaving source account)

    def test_transfer_with_memo(self, cli_runner):
        """Test transfer with memo (table output)."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_accounts = {
            "data": {
                "accounts": [
                    {"id": "acct-1", "name": "Account 1", "transfer_payee_id": "payee-1"},
                    {"id": "acct-2", "name": "Account 2", "transfer_payee_id": "payee-2"},
                ]
            }
        }

        mock_txn_response = {
            "data": {"transaction": {"id": "txn-1", "memo": "Monthly savings", "amount": -50000}}
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts)
                mock_client.create_transaction = AsyncMock(return_value=mock_txn_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "transfer",
                        "--from-account",
                        "Account 1",
                        "--to-account",
                        "Account 2",
                        "--amount",
                        "50.00",
                        "--date",
                        "2024-01-20",
                        "--memo",
                        "Monthly savings",
                    ],
                )

                assert result.exit_code == 0
                # Transfer command outputs table format (no --table flag available yet)
                assert "txn-1" in result.stdout
                # Verify API call
                call_kwargs = mock_client.create_transaction.call_args[1]
                assert call_kwargs["transaction"]["memo"] == "Monthly savings"

    def test_transfer_account_not_found(self, cli_runner):
        """Test transfer with invalid account name."""
        mock_settings = MagicMock()
        mock_settings.api_token = "test-token"
        mock_settings.budget_id = "budget-1"

        mock_accounts = {
            "data": {
                "accounts": [{"id": "acct-1", "name": "Checking", "transfer_payee_id": "payee-1"}]
            }
        }

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            with patch("ynab_cli.cli.transactions.YNABClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_accounts = AsyncMock(return_value=mock_accounts)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = cli_runner.invoke(
                    app,
                    [
                        "transactions",
                        "transfer",
                        "--from-account",
                        "InvalidAccount",
                        "--to-account",
                        "Checking",
                        "--amount",
                        "100.00",
                        "--date",
                        "2024-01-15",
                    ],
                )

                assert result.exit_code != 0
                assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_transfer_requires_token(self, cli_runner):
        """Test transfer requires API token."""
        mock_settings = MagicMock()
        mock_settings.api_token = None

        with patch("ynab_cli.cli.transactions.settings", mock_settings):
            result = cli_runner.invoke(
                app,
                [
                    "transactions",
                    "transfer",
                    "--from-account",
                    "Checking",
                    "--to-account",
                    "Savings",
                    "--amount",
                    "100.00",
                    "--date",
                    "2024-01-15",
                ],
            )

            assert result.exit_code != 0
            assert "token" in result.stdout.lower() or "login" in result.stdout.lower()
