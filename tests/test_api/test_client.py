"""Tests for YNAB API client."""

import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from ynab_cli.api.client import YNABClient


class TestYNABClientInit:
    """Tests for YNABClient initialization."""

    def test_init_with_explicit_token_and_budget(self):
        """Client should initialize with explicit API token and budget ID."""
        client = YNABClient(api_token="test-token-123", budget_id="budget-456")

        assert client.api_token == "test-token-123"
        assert client.budget_id == "budget-456"
        assert client.base_url == "https://api.ynab.com/v1"
        assert isinstance(client.client, httpx.AsyncClient)

    def test_init_requires_api_token(self, clean_env):
        """Client should raise ValueError if no API token is provided."""
        with patch("ynab_cli.api.client.settings", None):
            with pytest.raises(ValueError, match="YNAB API token is required"):
                YNABClient(api_token=None, budget_id="budget-123")

    def test_init_requires_budget_id_by_default(self, clean_env):
        """Client should raise ValueError if no budget ID is provided by default."""
        with patch("ynab_cli.api.client.settings", None):
            with pytest.raises(ValueError, match="Budget ID is required"):
                YNABClient(api_token="test-token")

    def test_init_can_skip_budget_requirement(self, clean_env):
        """Client should allow initialization without budget_id when require_budget=False."""
        with patch("ynab_cli.api.client.settings", None):
            client = YNABClient(api_token="test-token", require_budget=False)

            assert client.api_token == "test-token"
            assert client.budget_id is None

    def test_init_sets_authorization_header(self):
        """Client should set Bearer token in Authorization header."""
        client = YNABClient(api_token="test-token-abc", budget_id="budget-123")

        headers = client.client.headers
        assert headers["Authorization"] == "Bearer test-token-abc"
        assert headers["Content-Type"] == "application/json"

    def test_init_accepts_custom_base_url(self):
        """Client should accept custom base URL."""
        client = YNABClient(
            api_token="test-token", budget_id="budget-123", base_url="https://custom.api.com"
        )

        assert client.base_url == "https://custom.api.com"


class TestYNABClientAPIMethods:
    """Tests for YNABClient API methods."""

    @pytest.fixture
    def mock_client(self):
        """Fixture providing a YNABClient with mocked httpx client."""
        client = YNABClient(api_token="test-token", budget_id="default-budget-id")
        # Replace the httpx client with a mock
        client.client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_get_user(self, mock_client):
        """get_user should call /user endpoint and return parsed JSON."""
        expected_response = {"data": {"user": {"id": "user-123"}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_user()

        mock_client.client.get.assert_called_once_with("/user")
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_budgets_without_accounts(self, mock_client):
        """get_budgets should call /budgets without include_accounts param."""
        expected_response = {"data": {"budgets": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_budgets(include_accounts=False)

        mock_client.client.get.assert_called_once_with("/budgets", params={})
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_budgets_with_accounts(self, mock_client):
        """get_budgets should include accounts when requested."""
        expected_response = {"data": {"budgets": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_budgets(include_accounts=True)

        mock_client.client.get.assert_called_once_with(
            "/budgets", params={"include_accounts": "true"}
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_budget_uses_default_budget_id(self, mock_client):
        """get_budget should use client's default budget_id if not specified."""
        expected_response = {"data": {"budget": {"id": "default-budget-id"}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_budget()

        mock_client.client.get.assert_called_once_with("/budgets/default-budget-id")
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_budget_accepts_custom_budget_id(self, mock_client):
        """get_budget should accept custom budget_id parameter."""
        expected_response = {"data": {"budget": {"id": "custom-budget"}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_budget(budget_id="custom-budget")

        mock_client.client.get.assert_called_once_with("/budgets/custom-budget")
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_accounts(self, mock_client):
        """get_accounts should call correct endpoint with budget ID."""
        expected_response = {"data": {"accounts": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_accounts()

        mock_client.client.get.assert_called_once_with("/budgets/default-budget-id/accounts")
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_categories(self, mock_client):
        """get_categories should call correct endpoint with budget ID."""
        expected_response = {"data": {"category_groups": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_categories()

        mock_client.client.get.assert_called_once_with("/budgets/default-budget-id/categories")
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_month(self, mock_client):
        """get_month should call correct endpoint with month parameter."""
        expected_response = {"data": {"month": {"month": "2025-04-01"}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_month("2025-04-01")

        mock_client.client.get.assert_called_once_with(
            "/budgets/default-budget-id/months/2025-04-01"
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_payees(self, mock_client):
        """get_payees should call correct endpoint."""
        expected_response = {"data": {"payees": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_payees()

        mock_client.client.get.assert_called_once_with("/budgets/default-budget-id/payees")
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_transactions_without_filters(self, mock_client):
        """get_transactions should call endpoint without params when no filters."""
        expected_response = {"data": {"transactions": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_transactions()

        mock_client.client.get.assert_called_once_with(
            "/budgets/default-budget-id/transactions", params={}
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_transactions_with_since_date(self, mock_client):
        """get_transactions should pass since_date parameter."""
        expected_response = {"data": {"transactions": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_transactions(since_date="2025-01-01")

        mock_client.client.get.assert_called_once_with(
            "/budgets/default-budget-id/transactions", params={"since_date": "2025-01-01"}
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_get_transactions_with_type_filter(self, mock_client):
        """get_transactions should pass transaction_type parameter."""
        expected_response = {"data": {"transactions": []}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        result = await mock_client.get_transactions(transaction_type="unapproved")

        mock_client.client.get.assert_called_once_with(
            "/budgets/default-budget-id/transactions", params={"type": "unapproved"}
        )
        assert result == expected_response


class TestYNABClientErrorHandling:
    """Tests for YNABClient error handling."""

    @pytest.fixture
    def mock_client(self):
        """Fixture providing a YNABClient with mocked httpx client."""
        client = YNABClient(api_token="test-token", budget_id="default-budget-id")
        client.client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_handles_401_unauthorized(self, mock_client):
        """Client should propagate 401 Unauthorized errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        mock_client.client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get_budgets()

        assert exc_info.value.response.status_code == 401

    @pytest.mark.asyncio
    async def test_handles_403_forbidden(self, mock_client):
        """Client should propagate 403 Forbidden errors."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=Mock(), response=mock_response
        )
        mock_client.client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get_budget()

        assert exc_info.value.response.status_code == 403

    @pytest.mark.asyncio
    async def test_handles_404_not_found(self, mock_client):
        """Client should propagate 404 Not Found errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_client.client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get_budget(budget_id="nonexistent")

        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_handles_500_server_error(self, mock_client):
        """Client should propagate 500 Internal Server Error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response
        )
        mock_client.client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get_transactions()

        assert exc_info.value.response.status_code == 500

    @pytest.mark.asyncio
    async def test_handles_429_rate_limit(self, mock_client):
        """Client should propagate 429 Too Many Requests errors."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=Mock(), response=mock_response
        )
        mock_client.client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get_accounts()

        assert exc_info.value.response.status_code == 429

    @pytest.mark.asyncio
    async def test_handles_network_timeout(self, mock_client):
        """Client should propagate network timeout errors."""
        mock_client.client.get.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(httpx.TimeoutException):
            await mock_client.get_budgets()

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, mock_client):
        """Client should propagate connection errors."""
        mock_client.client.get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(httpx.ConnectError):
            await mock_client.get_user()

    @pytest.mark.asyncio
    async def test_raise_for_status_is_called_on_success(self, mock_client):
        """Client should call raise_for_status even on successful responses."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_client.client.get.return_value = mock_response

        await mock_client.get_budgets()

        # Verify raise_for_status was called
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_malformed_json_response_raises_error(self, mock_client):
        """Client should raise error when response is not valid JSON."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.client.get.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid JSON"):
            await mock_client.get_budgets()


class TestYNABClientContextManager:
    """Tests for YNABClient async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager_entry(self):
        """Client should return self on __aenter__."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")

        async with client as ctx_client:
            assert ctx_client is client

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_client(self):
        """Client should close httpx client on __aexit__."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")

        # Mock the close method to track if it's called
        client.client.aclose = AsyncMock()

        async with client:
            pass  # Exit context

        # Verify close was called
        client.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_on_exception(self):
        """Client should close httpx client even when exception occurs."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")

        # Mock the close method
        client.client.aclose = AsyncMock()

        # Raise exception inside context
        with pytest.raises(RuntimeError):
            async with client:
                raise RuntimeError("Test error")

        # Verify close was still called
        client.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method_closes_httpx_client(self):
        """close() method should close the underlying httpx client."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")

        # Mock aclose
        client.client.aclose = AsyncMock()

        await client.close()

        client.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_api_calls(self):
        """Context manager should work with actual API calls."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")

        # Mock httpx client
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"budgets": []}}
        mock_response.raise_for_status = Mock()
        client.client.get = AsyncMock(return_value=mock_response)
        client.client.aclose = AsyncMock()

        async with client:
            result = await client.get_budgets()
            assert result == {"data": {"budgets": []}}

        # Verify client was closed after context exit
        client.client.aclose.assert_called_once()


class TestYNABClientWriteOperations:
    """Tests for YNABClient write operations (POST/PUT/PATCH/DELETE)."""

    @pytest.fixture
    def mock_client(self):
        """Fixture providing a YNABClient with mocked httpx client."""
        client = YNABClient(api_token="test-token", budget_id="default-budget-id")
        client.client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_create_transaction(self, mock_client):
        """create_transaction should POST with correct payload format."""
        transaction_data = {
            "account_id": "acc-123",
            "date": "2025-01-15",
            "amount": -5000,
            "payee_id": "payee-456",
            "category_id": "cat-789",
            "memo": "Test transaction",
            "cleared": "cleared",
            "approved": True,
        }
        expected_response = {"data": {"transaction": transaction_data}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.post.return_value = mock_response

        result = await mock_client.create_transaction(transaction_data)

        # Verify POST was called with correct endpoint and payload
        mock_client.client.post.assert_called_once_with(
            "/budgets/default-budget-id/transactions", json={"transaction": transaction_data}
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_create_transaction_with_custom_budget(self, mock_client):
        """create_transaction should use custom budget_id when provided."""
        transaction_data = {"account_id": "acc-123", "date": "2025-01-15", "amount": 1000}
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_client.client.post.return_value = mock_response

        await mock_client.create_transaction(transaction_data, budget_id="custom-budget")

        mock_client.client.post.assert_called_once_with(
            "/budgets/custom-budget/transactions", json={"transaction": transaction_data}
        )

    @pytest.mark.asyncio
    async def test_update_transaction(self, mock_client):
        """update_transaction should PUT with correct payload format."""
        transaction_id = "txn-123"
        updates = {"category_id": "new-cat-456", "approved": True, "memo": "Updated memo"}
        expected_response = {"data": {"transaction": {"id": transaction_id}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.put.return_value = mock_response

        result = await mock_client.update_transaction(transaction_id, **updates)

        # Verify PUT was called with correct endpoint and payload
        mock_client.client.put.assert_called_once_with(
            "/budgets/default-budget-id/transactions/txn-123", json={"transaction": updates}
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_update_transaction_with_custom_budget(self, mock_client):
        """update_transaction should use custom budget_id when provided."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_client.client.put.return_value = mock_response

        await mock_client.update_transaction("txn-123", budget_id="custom-budget", approved=True)

        mock_client.client.put.assert_called_once_with(
            "/budgets/custom-budget/transactions/txn-123", json={"transaction": {"approved": True}}
        )

    @pytest.mark.asyncio
    async def test_delete_transaction(self, mock_client):
        """delete_transaction should DELETE at correct endpoint."""
        transaction_id = "txn-789"
        expected_response = {"data": {"transaction": {"id": transaction_id, "deleted": True}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.delete.return_value = mock_response

        result = await mock_client.delete_transaction(transaction_id)

        # Verify DELETE was called with correct endpoint
        mock_client.client.delete.assert_called_once_with(
            "/budgets/default-budget-id/transactions/txn-789"
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_delete_transaction_with_custom_budget(self, mock_client):
        """delete_transaction should use custom budget_id when provided."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_client.client.delete.return_value = mock_response

        await mock_client.delete_transaction("txn-123", budget_id="custom-budget")

        mock_client.client.delete.assert_called_once_with(
            "/budgets/custom-budget/transactions/txn-123"
        )

    @pytest.mark.asyncio
    async def test_update_category(self, mock_client):
        """update_category should PATCH with correct payload format."""
        category_id = "cat-123"
        updates = {"name": "New Category Name", "note": "Updated note", "goal_target": 50000}
        expected_response = {"data": {"category": {"id": category_id}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.patch.return_value = mock_response

        result = await mock_client.update_category(category_id, **updates)

        # Verify PATCH was called with correct endpoint and payload
        mock_client.client.patch.assert_called_once_with(
            "/budgets/default-budget-id/categories/cat-123", json={"category": updates}
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_update_category_with_custom_budget(self, mock_client):
        """update_category should use custom budget_id when provided."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_client.client.patch.return_value = mock_response

        await mock_client.update_category("cat-123", budget_id="custom-budget", name="New Name")

        mock_client.client.patch.assert_called_once_with(
            "/budgets/custom-budget/categories/cat-123", json={"category": {"name": "New Name"}}
        )

    @pytest.mark.asyncio
    async def test_update_category_month(self, mock_client):
        """update_category_month should PATCH month-specific category data."""
        category_id = "cat-456"
        month = "2025-04-01"
        updates = {"budgeted": 25000}
        expected_response = {"data": {"category": {"id": category_id, "budgeted": 25000}}}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client.client.patch.return_value = mock_response

        result = await mock_client.update_category_month(category_id, month, **updates)

        # Verify PATCH was called with correct month-specific endpoint
        mock_client.client.patch.assert_called_once_with(
            "/budgets/default-budget-id/months/2025-04-01/categories/cat-456",
            json={"category": updates},
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_update_category_month_with_custom_budget(self, mock_client):
        """update_category_month should use custom budget_id when provided."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_client.client.patch.return_value = mock_response

        await mock_client.update_category_month(
            "cat-123", "2025-05-01", budget_id="custom-budget", budgeted=10000
        )

        mock_client.client.patch.assert_called_once_with(
            "/budgets/custom-budget/months/2025-05-01/categories/cat-123",
            json={"category": {"budgeted": 10000}},
        )


class TestRateLimiting:
    """Tests for rate limiting with aiolimiter."""

    @pytest.fixture
    def mock_client_fast(self, mock_rate_limiter):
        """Fixture providing a YNABClient with mocked rate limiter for fast tests."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")
        # Replace limiter with instant-pass version
        client.limiter = mock_rate_limiter
        # Mock HTTP client
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        client.client.get = AsyncMock(return_value=mock_response)
        return client

    @pytest.mark.asyncio
    async def test_rate_limiting_isolated_per_instance(self, mock_rate_limiter):
        """Rate limiting should be isolated per client instance."""
        # Create two separate client instances
        client1 = YNABClient(api_token="token1", budget_id="budget1")
        client2 = YNABClient(api_token="token2", budget_id="budget2")

        # Mock their rate limiters for fast tests
        client1.limiter = mock_rate_limiter
        client2.limiter = mock_rate_limiter

        # Mock their HTTP clients
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()

        client1.client.get = AsyncMock(return_value=mock_response)
        client2.client.get = AsyncMock(return_value=mock_response)

        # Make rapid calls with both clients - should be instant with mocked limiter
        start = time.time()
        await client1.get_budgets()
        await client1.get_budgets()
        await client2.get_budgets()
        await client2.get_budgets()
        total_time = time.time() - start

        # All calls should be instant (mocked limiter)
        assert total_time < 0.1, (
            f"All calls took {total_time}s, should be instant with mocked limiter"
        )

    @pytest.mark.asyncio
    async def test_client_has_limiter_configured(self):
        """Client should have rate limiter configured on initialization."""
        from aiolimiter import AsyncLimiter

        client = YNABClient(api_token="test-token", budget_id="test-budget")

        assert hasattr(client, "limiter")
        assert isinstance(client.limiter, AsyncLimiter)

    @pytest.mark.asyncio
    async def test_limiter_has_correct_rate(self):
        """Rate limiter should be configured for 200 requests per hour."""
        client = YNABClient(api_token="test-token", budget_id="test-budget")

        # Check limiter configuration (200 req/hour = 3600 second period)
        assert client.limiter.max_rate == 200
        assert client.limiter.time_period == 3600
