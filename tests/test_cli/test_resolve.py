"""Tests for name-to-ID resolution helpers."""

from unittest.mock import AsyncMock, patch

import pytest

from ynab_cli.cli.resolve import resolve_category_name, resolve_payee_name


@pytest.fixture
def mock_categories_response():
    """Mock categories API response."""
    return {
        "data": {
            "category_groups": [
                {
                    "id": "group-1",
                    "name": "Monthly Bills",
                    "hidden": False,
                    "deleted": False,
                    "categories": [
                        {"id": "cat-1", "name": "Groceries", "hidden": False, "deleted": False},
                        {"id": "cat-2", "name": "Electric", "hidden": False, "deleted": False},
                        {"id": "cat-3", "name": "Hidden Cat", "hidden": True, "deleted": False},
                    ],
                },
                {
                    "id": "group-2",
                    "name": "Fun Money",
                    "hidden": False,
                    "deleted": False,
                    "categories": [
                        {"id": "cat-4", "name": "Dining Out", "hidden": False, "deleted": False},
                    ],
                },
                {
                    "id": "group-hidden",
                    "name": "Hidden Group",
                    "hidden": True,
                    "deleted": False,
                    "categories": [
                        {"id": "cat-5", "name": "Groceries", "hidden": False, "deleted": False},
                    ],
                },
            ]
        }
    }


@pytest.fixture
def mock_payees_response():
    """Mock payees API response."""
    return {
        "data": {
            "payees": [
                {"id": "payee-1", "name": "Amazon", "deleted": False},
                {"id": "payee-2", "name": "Venmo", "deleted": False},
                {"id": "payee-3", "name": "Walmart", "deleted": False},
                {"id": "payee-4", "name": "Deleted Payee", "deleted": True},
            ]
        }
    }


class TestResolveCategoryName:
    """Tests for resolve_category_name."""

    def test_resolves_exact_match(self, mock_categories_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = resolve_category_name("Groceries")
            assert result == "cat-1"

    def test_case_insensitive(self, mock_categories_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = resolve_category_name("groceries")
            assert result == "cat-1"

    def test_not_found_raises(self, mock_categories_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Category not found"):
                resolve_category_name("Nonexistent")

    def test_skips_hidden_categories(self, mock_categories_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Category not found"):
                resolve_category_name("Hidden Cat")

    def test_skips_hidden_groups(self, mock_categories_response):
        """Category in hidden group should not match, so 'Groceries' resolves to cat-1 only."""
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Only one "Groceries" should be found (cat-1), not cat-5 from hidden group
            result = resolve_category_name("Groceries")
            assert result == "cat-1"

    def test_passes_budget_id(self, mock_categories_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_categories = AsyncMock(return_value=mock_categories_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            resolve_category_name("Electric", budget_id="budget-2")
            mock_client.get_categories.assert_called_once_with(budget_id="budget-2")


class TestResolvePayeeName:
    """Tests for resolve_payee_name."""

    def test_resolves_exact_match(self, mock_payees_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = resolve_payee_name("Amazon")
            assert result == "payee-1"

    def test_case_insensitive(self, mock_payees_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = resolve_payee_name("amazon")
            assert result == "payee-1"

    def test_not_found_raises(self, mock_payees_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Payee not found"):
                resolve_payee_name("Nonexistent")

    def test_skips_deleted_payees(self, mock_payees_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Payee not found"):
                resolve_payee_name("Deleted Payee")

    def test_passes_budget_id(self, mock_payees_response):
        with patch("ynab_cli.cli.resolve.YNABClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_payees = AsyncMock(return_value=mock_payees_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            resolve_payee_name("Venmo", budget_id="budget-2")
            mock_client.get_payees.assert_called_once_with(budget_id="budget-2")
