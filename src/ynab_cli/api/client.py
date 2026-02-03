"""YNAB API client - direct HTTP calls without MCP layer."""

import time
from typing import Any, cast

import httpx
from aiolimiter import AsyncLimiter

from ynab_cli.config import settings
from ynab_cli.logging_config import log_api_request, log_api_response


class YNABClient:
    """
    Direct YNAB API client for budget operations.

    This client makes direct HTTP calls to the YNAB API without any MCP layer.
    Designed for use with Claude Code or CLI tools.
    """

    def __init__(
        self,
        api_token: str | None = None,
        budget_id: str | None = None,
        base_url: str | None = None,
        require_budget: bool = True,
    ):
        """
        Initialize YNAB API client.

        Args:
            api_token: YNAB API token (defaults to settings)
            budget_id: Default budget ID (defaults to settings)
            base_url: API base URL (defaults to settings)
            require_budget: Whether budget_id is required (default True)
        """
        self.api_token = api_token or (settings.api_token if settings else None)
        self.budget_id = budget_id or (settings.budget_id if settings else None)
        self.base_url = base_url or "https://api.ynab.com/v1"

        if not self.api_token:
            raise ValueError("YNAB API token is required")
        if require_budget and not self.budget_id:
            raise ValueError("Budget ID is required")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        # Rate limiter: 200 requests per hour (YNAB API limit)
        self.limiter = AsyncLimiter(max_rate=200, time_period=3600)

    async def __aenter__(self) -> "YNABClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    # Core API methods

    async def get_user(self) -> dict[str, Any]:
        """Get authenticated user information."""
        async with self.limiter:
            response = await self.client.get("/user")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_budgets(self, include_accounts: bool = False) -> dict[str, Any]:
        """
        Get list of budgets.

        Args:
            include_accounts: Include account details

        Returns:
            Budget list response
        """
        params = {}
        if include_accounts:
            params["include_accounts"] = "true"

        # Log request
        log_api_request("GET", f"{self.base_url}/budgets", params if params else None)

        # Make request with rate limiting
        async with self.limiter:
            start_time = time.time()
            response = await self.client.get("/budgets", params=params)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            log_api_response(response.status_code, f"{self.base_url}/budgets", duration_ms)

            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_budget(self, budget_id: str | None = None) -> dict[str, Any]:
        """
        Get specific budget details.

        Args:
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Budget details response
        """
        bid = budget_id or self.budget_id
        async with self.limiter:
            response = await self.client.get(f"/budgets/{bid}")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_accounts(self, budget_id: str | None = None) -> dict[str, Any]:
        """
        Get accounts for a budget.

        Args:
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Accounts response
        """
        bid = budget_id or self.budget_id
        async with self.limiter:
            response = await self.client.get(f"/budgets/{bid}/accounts")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_categories(self, budget_id: str | None = None) -> dict[str, Any]:
        """
        Get categories for a budget.

        Args:
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Categories response
        """
        bid = budget_id or self.budget_id
        async with self.limiter:
            response = await self.client.get(f"/budgets/{bid}/categories")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_month(self, month: str, budget_id: str | None = None) -> dict[str, Any]:
        """
        Get budget data for a specific month, including category balances.

        Args:
            month: Month in YYYY-MM-01 format (e.g., '2025-04-01')
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Month response with category data
        """
        bid = budget_id or self.budget_id
        async with self.limiter:
            response = await self.client.get(f"/budgets/{bid}/months/{month}")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_payees(self, budget_id: str | None = None) -> dict[str, Any]:
        """
        Get payees for a budget.

        Args:
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Payees response
        """
        bid = budget_id or self.budget_id
        async with self.limiter:
            response = await self.client.get(f"/budgets/{bid}/payees")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def get_transactions(
        self,
        budget_id: str | None = None,
        since_date: str | None = None,
        transaction_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Get transactions for a budget.

        Args:
            budget_id: Budget ID (defaults to configured budget)
            since_date: Only transactions after this date (YYYY-MM-DD)
            transaction_type: Filter by type (e.g., 'unapproved')

        Returns:
            Transactions response
        """
        bid = budget_id or self.budget_id
        params = {}
        if since_date:
            params["since_date"] = since_date
        if transaction_type:
            params["type"] = transaction_type

        async with self.limiter:
            response = await self.client.get(f"/budgets/{bid}/transactions", params=params)
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def update_transaction(
        self, transaction_id: str, budget_id: str | None = None, **updates: Any
    ) -> dict[str, Any]:
        """
        Update a transaction.

        Args:
            transaction_id: Transaction ID
            budget_id: Budget ID (defaults to configured budget)
            **updates: Fields to update (category_id, approved, memo, etc.)

        Returns:
            Updated transaction response
        """
        bid = budget_id or self.budget_id

        # Build update payload
        payload = {"transaction": updates}

        async with self.limiter:
            response = await self.client.put(
                f"/budgets/{bid}/transactions/{transaction_id}", json=payload
            )
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def delete_transaction(
        self, transaction_id: str, budget_id: str | None = None
    ) -> dict[str, Any]:
        """
        Delete a transaction.

        Args:
            transaction_id: Transaction ID
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Deletion response
        """
        bid = budget_id or self.budget_id

        async with self.limiter:
            response = await self.client.delete(f"/budgets/{bid}/transactions/{transaction_id}")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def update_category(
        self, category_id: str, budget_id: str | None = None, **updates: Any
    ) -> dict[str, Any]:
        """
        Update a category.

        Args:
            category_id: Category ID
            budget_id: Budget ID (defaults to configured budget)
            **updates: Fields to update (name, note, goal_target, etc.)

        Returns:
            Updated category response
        """
        bid = budget_id or self.budget_id

        # Build update payload
        payload = {"category": updates}

        async with self.limiter:
            response = await self.client.patch(
                f"/budgets/{bid}/categories/{category_id}", json=payload
            )
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def update_category_month(
        self, category_id: str, month: str, budget_id: str | None = None, **updates: Any
    ) -> dict[str, Any]:
        """
        Update category budgeted amount for a specific month.

        Args:
            category_id: Category ID
            month: Month in YYYY-MM-01 format
            budget_id: Budget ID (defaults to configured budget)
            **updates: Fields to update (budgeted, etc.)

        Returns:
            Updated category month response
        """
        bid = budget_id or self.budget_id

        # Build update payload
        payload = {"category": updates}

        async with self.limiter:
            response = await self.client.patch(
                f"/budgets/{bid}/months/{month}/categories/{category_id}", json=payload
            )
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def create_transaction(
        self, transaction: dict[str, Any], budget_id: str | None = None
    ) -> dict[str, Any]:
        """
        Create a new transaction.

        Args:
            transaction: Transaction data dict with required fields:
                - account_id: Account ID
                - date: ISO date (YYYY-MM-DD)
                - amount: Amount in milliunits (integer)
                Optional fields:
                - payee_id: Payee ID
                - category_id: Category ID
                - memo: Transaction memo
                - cleared: Cleared status ('cleared', 'uncleared', 'reconciled')
                - approved: Boolean
            budget_id: Budget ID (defaults to configured budget)

        Returns:
            Created transaction response
        """
        bid = budget_id or self.budget_id

        # Wrap transaction in required format
        payload = {"transaction": transaction}

        async with self.limiter:
            response = await self.client.post(f"/budgets/{bid}/transactions", json=payload)
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())


# Convenience function for quick one-off operations
async def get_ynab_client() -> YNABClient:
    """
    Get a YNAB client instance with default settings.

    Usage:
        async with get_ynab_client() as client:
            transactions = await client.get_transactions()
    """
    return YNABClient()
