"""Transaction commands for the YNAB CLI."""

import asyncio
import json
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

from ynab_cli.api.client import YNABClient
from ynab_cli.cli.resolve import resolve_category_name, resolve_payee_name
from ynab_cli.config import settings
from ynab_cli.error_handling import (
    YNABAPIError,
    YNABAuthenticationError,
    YNABNetworkError,
    format_api_error,
    get_error_details,
)
from ynab_cli.utils import convert_monetary_fields, dollars_to_milliunits, milliunits_to_dollars

transactions_app = typer.Typer(
    name="transactions",
    help="Manage transactions",
    no_args_is_help=True,
)

console = Console()


def handle_cli_error(error: Exception) -> None:
    """
    Handle CLI errors with specific error messages.

    Args:
        error: The exception to handle
    """
    if isinstance(error, YNABAuthenticationError):
        console.print(f"[red]Authentication Error:[/red] {error.message}")
        console.print("Run 'ynab login' to configure your API token")
    elif isinstance(error, YNABNetworkError):
        console.print(f"[red]Network Error:[/red] {error.message}")
    elif isinstance(error, YNABAPIError):
        console.print(f"[red]API Error:[/red] {error.message}")
        if error.status_code:
            console.print(f"Status code: {error.status_code}")
    elif isinstance(error, (httpx.HTTPStatusError, httpx.RequestError, ValueError)):
        # Convert to specific YNAB error
        ynab_error = format_api_error(error)
        console.print(f"[red]Error:[/red] {ynab_error}")
    else:
        console.print(f"[red]Unexpected Error:[/red] {error!s}")

    # Show detailed debug info if debug mode is enabled
    details = get_error_details(error)
    if details != str(error):  # Only print if we have additional debug info
        console.print("\n[yellow]Debug Details:[/yellow]")
        console.print(details)


@transactions_app.command("list")
def list_transactions(
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    since_date: str | None = typer.Option(
        None,
        "--since-date",
        help="Only transactions on or after this date (YYYY-MM-DD)",
    ),
    transaction_type: str | None = typer.Option(
        None,
        "--type",
        help="Filter by type: 'unapproved', 'uncategorized', or 'unapproved,uncategorized'",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Maximum number of transactions to show (client-side filter, use --since-date to limit API fetch)",
    ),
    table_output: bool = typer.Option(
        False,
        "--table",
        help="Output as table (default is JSON)",
    ),
) -> None:
    """
    List transactions for a budget.

    Shows transaction date, payee, category, amount, and cleared status.
    Amounts are displayed in dollars (negative = expense, positive = income).
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Run async operation
        response = asyncio.run(
            _list_transactions_async(
                budget_id=budget,
                since_date=since_date,
                transaction_type=transaction_type,
            )
        )

        # Extract transactions from response
        transactions = response["data"]["transactions"]

        # Apply limit if specified
        if limit:
            transactions = transactions[:limit]

        # Output
        if table_output:
            # Table output
            _print_transactions_table(transactions)
        else:
            # JSON output (default) - convert milliunits to dollars
            output = convert_monetary_fields({"transactions": transactions})
            print(json.dumps(output, indent=2))

    except Exception as e:
        handle_cli_error(e)
        raise typer.Exit(1) from None


async def _list_transactions_async(
    budget_id: str | None,
    since_date: str | None,
    transaction_type: str | None,
) -> dict[str, Any]:
    """Async helper to fetch transactions.

    When transaction_type contains multiple comma-separated values (e.g. 'unapproved,uncategorized'),
    makes a separate API call for each type and merges results, deduplicating by transaction ID.
    The YNAB API only accepts a single type value per request.
    """
    async with YNABClient() as client:
        if transaction_type and "," in transaction_type:
            types = [t.strip() for t in transaction_type.split(",")]
            results = await asyncio.gather(
                *[
                    client.get_transactions(
                        budget_id=budget_id,
                        since_date=since_date,
                        transaction_type=t,
                    )
                    for t in types
                ]
            )
            seen: set[str] = set()
            merged: list[Any] = []
            for result in results:
                for txn in result["data"]["transactions"]:
                    if txn["id"] not in seen:
                        seen.add(txn["id"])
                        merged.append(txn)
            # Return in the same shape as a single API response
            return {"data": {"transactions": merged}}

        return await client.get_transactions(
            budget_id=budget_id,
            since_date=since_date,
            transaction_type=transaction_type,
        )


def _print_transactions_table(transactions: list) -> None:
    """Print transactions in table format."""
    table = Table(title="Transactions")
    table.add_column("Date", style="cyan")
    table.add_column("Payee", style="green")
    table.add_column("Category", style="blue")
    table.add_column("Amount", style="yellow", justify="right")
    table.add_column("Cleared", style="magenta", justify="center")

    for txn in transactions:
        # Convert milliunits to dollars
        amount = milliunits_to_dollars(txn["amount"])

        # Format amount as currency
        amount_str = f"${amount:,.2f}"

        # Get category name (may be None for uncategorized)
        category = txn.get("category_name") or "[dim]Uncategorized[/dim]"

        # Cleared status
        cleared = txn.get("cleared", "")
        if cleared == "cleared":
            cleared_display = "✓"
        elif cleared == "uncleared":
            cleared_display = ""
        else:
            cleared_display = cleared

        table.add_row(
            txn["date"],
            txn.get("payee_name", ""),
            category,
            amount_str,
            cleared_display,
        )

    console.print(table)


@transactions_app.command("create")
def create_transaction(
    account: str = typer.Option(
        ...,
        "--account",
        help="Account ID",
    ),
    date: str = typer.Option(
        ...,
        "--date",
        help="Transaction date (YYYY-MM-DD)",
    ),
    amount: float = typer.Option(
        ...,
        "--amount",
        help="Amount in dollars (negative for expenses, positive for income)",
    ),
    payee: str | None = typer.Option(
        None,
        "--payee",
        help="Payee ID",
    ),
    payee_name: str | None = typer.Option(
        None,
        "--payee-name",
        help="Payee name (resolved to ID, alternative to --payee)",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Category ID",
    ),
    category_name: str | None = typer.Option(
        None,
        "--category-name",
        help="Category name (resolved to ID, alternative to --category)",
    ),
    memo: str | None = typer.Option(
        None,
        "--memo",
        help="Transaction memo",
    ),
    cleared: bool = typer.Option(
        False,
        "--cleared",
        help="Mark transaction as cleared",
    ),
    approved: bool = typer.Option(
        False,
        "--approved",
        help="Mark transaction as approved",
    ),
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    table_output: bool = typer.Option(
        False,
        "--table",
        help="Output as table (default is JSON)",
    ),
) -> None:
    """
    Create a new transaction.

    Amounts should be in dollars (negative for expenses, positive for income).
    The CLI will automatically convert to milliunits for the API.

    Use --payee-name or --category-name to look up by name instead of ID.

    Examples:
        # Create an expense
        ynab transactions create --account acct-123 --date 2024-01-15 --amount -12.45

        # Create with names instead of IDs
        ynab transactions create --account acct-123 --date 2024-01-20 \\
            --amount -12.45 --payee-name "Amazon" --category-name "Groceries"

        # Create income with all fields
        ynab transactions create --account acct-123 --date 2024-01-20 \\
            --amount 100.00 --payee payee-456 --category cat-789 \\
            --memo "Freelance work" --cleared --approved
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Resolve names to IDs
        if payee_name:
            if payee:
                console.print("[red]Error: Cannot use both --payee and --payee-name[/red]")
                raise typer.Exit(1) from None
            try:
                payee = resolve_payee_name(payee_name, budget_id=budget)
            except ValueError:
                # Payee doesn't exist yet — pass payee_name directly so YNAB auto-creates it
                pass

        if category_name:
            if category:
                console.print("[red]Error: Cannot use both --category and --category-name[/red]")
                raise typer.Exit(1) from None
            category = resolve_category_name(category_name, budget_id=budget)

        # Convert amount to milliunits
        amount_milliunits = dollars_to_milliunits(amount)

        # Build transaction object
        transaction = {
            "account_id": account,
            "date": date,
            "amount": amount_milliunits,
        }

        # Add optional fields
        if payee:
            transaction["payee_id"] = payee
        elif payee_name:
            # payee_name was given but not found — pass directly for YNAB auto-creation
            transaction["payee_name"] = payee_name
        if category:
            transaction["category_id"] = category
        if memo:
            transaction["memo"] = memo
        if cleared:
            transaction["cleared"] = "cleared"
        if approved:
            transaction["approved"] = True

        # Run async operation
        response = asyncio.run(
            _create_transaction_async(
                budget_id=budget,
                transaction=transaction,
            )
        )

        # Extract created transaction
        created = response["data"]["transaction"]

        # Output
        if table_output:
            console.print("[green]✓ Transaction created successfully[/green]")
            console.print(f"ID: {created['id']}")
            console.print(f"Date: {created['date']}")
            console.print(f"Amount: ${milliunits_to_dollars(created['amount']):,.2f}")
        else:
            # JSON output (default) - convert milliunits to dollars
            output = convert_monetary_fields({"transaction": created})
            print(json.dumps(output, indent=2))

    except Exception as e:
        handle_cli_error(e)
        raise typer.Exit(1) from None


async def _create_transaction_async(
    budget_id: str | None,
    transaction: dict,
) -> dict[str, Any]:
    """Async helper to create a transaction."""
    async with YNABClient() as client:
        return await client.create_transaction(
            budget_id=budget_id,
            transaction=transaction,
        )


@transactions_app.command("update")
def update_transaction(
    transaction_id: str = typer.Argument(
        ...,
        help="Transaction ID to update",
    ),
    account: str | None = typer.Option(
        None,
        "--account",
        help="Account ID",
    ),
    date: str | None = typer.Option(
        None,
        "--date",
        help="Transaction date (YYYY-MM-DD)",
    ),
    amount: float | None = typer.Option(
        None,
        "--amount",
        help="Amount in dollars",
    ),
    payee: str | None = typer.Option(
        None,
        "--payee",
        help="Payee ID",
    ),
    payee_name: str | None = typer.Option(
        None,
        "--payee-name",
        help="Payee name (resolved to ID, alternative to --payee)",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help='Category ID (use empty string "" to clear/uncategorize)',
    ),
    category_name: str | None = typer.Option(
        None,
        "--category-name",
        help="Category name (resolved to ID, alternative to --category)",
    ),
    memo: str | None = typer.Option(
        None,
        "--memo",
        help="Transaction memo",
    ),
    cleared: bool = typer.Option(
        False,
        "--cleared",
        help="Mark transaction as cleared",
    ),
    approved: bool = typer.Option(
        False,
        "--approved",
        help="Mark transaction as approved",
    ),
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    table_output: bool = typer.Option(
        False,
        "--table",
        help="Output as table (default is JSON)",
    ),
) -> None:
    """
    Update an existing transaction.

    Provide only the fields you want to update. Fields not specified will remain unchanged.
    Use --payee-name or --category-name to look up by name instead of ID.

    Examples:
        # Update amount
        ynab transactions update txn-123 --amount -25.00

        # Recategorize by name
        ynab transactions update txn-123 --category-name "Groceries" --approved

        # Update multiple fields
        ynab transactions update txn-123 --amount -30.00 --memo "Updated" --cleared

        # Clear category (set to uncategorized)
        ynab transactions update txn-123 --category ""
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Resolve names to IDs
        if payee_name:
            if payee:
                console.print("[red]Error: Cannot use both --payee and --payee-name[/red]")
                raise typer.Exit(1) from None
            payee = resolve_payee_name(payee_name, budget_id=budget)

        if category_name:
            if category:
                console.print("[red]Error: Cannot use both --category and --category-name[/red]")
                raise typer.Exit(1) from None
            category = resolve_category_name(category_name, budget_id=budget)

        # Build updates object
        updates: dict[str, Any] = {}

        if account:
            updates["account_id"] = account
        if date:
            updates["date"] = date
        if amount is not None:
            updates["amount"] = dollars_to_milliunits(amount)
        if payee:
            updates["payee_id"] = payee
        if category is not None:
            updates["category_id"] = category or None
        if memo:
            updates["memo"] = memo
        if cleared:
            updates["cleared"] = "cleared"
        if approved:
            updates["approved"] = True

        # Run async operation
        response = asyncio.run(
            _update_transaction_async(
                transaction_id=transaction_id,
                budget_id=budget,
                updates=updates,
            )
        )

        # Extract updated transaction
        updated = response["data"]["transaction"]

        # Output
        if table_output:
            console.print("[green]✓ Transaction updated successfully[/green]")
            console.print(f"ID: {updated['id']}")
        else:
            # JSON output (default) - convert milliunits to dollars
            output = convert_monetary_fields({"transaction": updated})
            print(json.dumps(output, indent=2))

    except Exception as e:
        handle_cli_error(e)
        raise typer.Exit(1) from None


async def _update_transaction_async(
    transaction_id: str,
    budget_id: str | None,
    updates: dict,
) -> dict[str, Any]:
    """Async helper to update a transaction."""
    async with YNABClient() as client:
        return await client.update_transaction(
            transaction_id=transaction_id,
            budget_id=budget_id,
            **updates,
        )


@transactions_app.command("delete")
def delete_transaction(
    transaction_id: str = typer.Argument(
        ...,
        help="Transaction ID to delete",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Skip confirmation prompt",
    ),
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
) -> None:
    """
    Delete a transaction.

    By default, prompts for confirmation. Use --confirm to skip the prompt.

    Examples:
        # Delete with confirmation prompt
        ynab transactions delete txn-123

        # Delete without prompt
        ynab transactions delete txn-123 --confirm
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    # Prompt for confirmation if not provided
    if not confirm:
        confirmed = typer.confirm(f"Are you sure you want to delete transaction {transaction_id}?")
        if not confirmed:
            console.print("Cancelled")
            raise typer.Exit(0)

    try:
        # Run async operation
        asyncio.run(
            _delete_transaction_async(
                transaction_id=transaction_id,
                budget_id=budget,
            )
        )

        console.print(f"[green]✓ Transaction {transaction_id} deleted successfully[/green]")

    except Exception as e:
        handle_cli_error(e)
        raise typer.Exit(1) from None


async def _delete_transaction_async(
    transaction_id: str,
    budget_id: str | None,
) -> dict[str, Any]:
    """Async helper to delete a transaction."""
    async with YNABClient() as client:
        return await client.delete_transaction(
            transaction_id=transaction_id,
            budget_id=budget_id,
        )


def _parse_split_spec(spec: str) -> tuple[str | None, str, str | None]:
    """
    Parse a --split value into (amount_str, category_name, memo).

    Format: "amount:category[:memo]"
    Fill-remainder form: ":category[:memo]" (empty amount)
    """
    parts = spec.split(":", 2)
    if len(parts) < 2:
        raise ValueError(f"Invalid --split format '{spec}': expected 'amount:category[:memo]'")
    amount_str = parts[0].strip() or None
    category = parts[1].strip()
    memo = parts[2].strip() if len(parts) == 3 and parts[2].strip() else None
    if not category:
        raise ValueError(f"Invalid --split format '{spec}': category name is required")
    return amount_str, category, memo


@transactions_app.command("split")
def split_transaction(
    transaction_id: str = typer.Argument(
        ...,
        help="Transaction ID to split",
    ),
    split: list[str] = typer.Option(
        ...,
        "--split",
        help=(
            "Split specification: 'amount:category[:memo]'. "
            "Repeat for each split. "
            "Last split may use ':category' (no amount) to fill the remainder. "
            "Example: --split '30.00:Pets' --split ':Home Improvement'"
        ),
    ),
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
) -> None:
    """
    Split a transaction across multiple categories.

    Fetches the existing transaction, validates the split amounts, resolves
    category names, and updates the transaction with subtransactions.

    The YNAB API does not allow modifying subtransactions on an already-split
    transaction. If the transaction is already split, delete it in YNAB and
    recreate it.

    Examples:
        # Split with explicit amounts
        ynab transactions split txn-123 \\
            --split "30.00:Pets" \\
            --split "42.71:Home Improvement"

        # Fill remainder on last split
        ynab transactions split txn-123 \\
            --split "30.00:Pets" \\
            --split ":Home Improvement"

        # With per-split memo
        ynab transactions split txn-123 \\
            --split "30.00:Pets:vet supplies" \\
            --split ":Home Improvement"
    """
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    if len(split) < 2:
        console.print("[red]Error: At least 2 --split values are required[/red]")
        raise typer.Exit(1) from None

    try:
        # Parse split specs
        specs: list[tuple[str | None, str, str | None]] = []
        for s in split:
            specs.append(_parse_split_spec(s))

        # Validate: only the last split may be a fill-remainder
        for i, (amount_str, cat, _) in enumerate(specs[:-1]):
            if amount_str is None:
                console.print(
                    f"[red]Error: Only the last --split may omit the amount (fill remainder). "
                    f"Split {i + 1} has no amount.[/red]"
                )
                raise typer.Exit(1) from None

        # Fetch the parent transaction
        parent_response = asyncio.run(
            _get_transaction_async(transaction_id=transaction_id, budget_id=budget)
        )
        parent = parent_response["data"]["transaction"]

        # Error if already split
        if parent.get("subtransactions"):
            console.print(
                "[red]Error: This transaction is already split. "
                "Delete it in YNAB and recreate to re-split.[/red]"
            )
            raise typer.Exit(1) from None

        parent_amount = parent["amount"]  # milliunits, negative for expenses

        # Compute explicit amounts in milliunits and validate
        has_remainder = specs[-1][0] is None
        explicit_total = 0
        sub_amounts: list[int] = []

        for i, (amount_str, _cat, _memo) in enumerate(specs):
            if amount_str is None:
                # Placeholder — filled after loop
                sub_amounts.append(0)
                continue
            try:
                dollars = float(amount_str)
            except ValueError:
                console.print(f"[red]Error: Invalid amount '{amount_str}' in split {i + 1}[/red]")
                raise typer.Exit(1) from None
            # Match sign of parent
            millis = int(round(dollars * 1000))
            if parent_amount < 0:
                millis = -abs(millis)
            else:
                millis = abs(millis)
            sub_amounts.append(millis)
            explicit_total += millis

        if has_remainder:
            remainder = parent_amount - explicit_total
            if (parent_amount < 0 and remainder > 0) or (parent_amount >= 0 and remainder < 0):
                console.print(
                    f"[red]Error: Explicit split amounts (${abs(explicit_total) / 1000:.2f}) "
                    f"already exceed the transaction total (${abs(parent_amount) / 1000:.2f})[/red]"
                )
                raise typer.Exit(1) from None
            sub_amounts[-1] = remainder
        else:
            if explicit_total != parent_amount:
                console.print(
                    f"[red]Error: Split amounts total ${abs(explicit_total) / 1000:.2f} "
                    f"but transaction is ${abs(parent_amount) / 1000:.2f}. "
                    f"Amounts must sum exactly to the transaction total.[/red]"
                )
                raise typer.Exit(1) from None

        # Resolve category names and build subtransactions
        subtransactions = []
        for (amount_str, cat_name, memo), millis in zip(specs, sub_amounts):
            cat_id = resolve_category_name(cat_name, budget_id=budget)
            sub: dict[str, Any] = {"amount": millis, "category_id": cat_id}
            if memo:
                sub["memo"] = memo
            subtransactions.append(sub)

        # Update the transaction: null out category, add subtransactions
        response = asyncio.run(
            _update_transaction_async(
                transaction_id=transaction_id,
                budget_id=budget,
                updates={"category_id": None, "subtransactions": subtransactions},
            )
        )

        updated = response["data"]["transaction"]
        output = convert_monetary_fields({"transaction": updated})
        print(json.dumps(output, indent=2))

    except typer.Exit:
        raise
    except Exception as e:
        handle_cli_error(e)
        raise typer.Exit(1) from None


async def _get_transaction_async(
    transaction_id: str,
    budget_id: str | None,
) -> dict[str, Any]:
    """Async helper to fetch a single transaction."""
    async with YNABClient() as client:
        return await client.get_transaction(
            transaction_id=transaction_id,
            budget_id=budget_id,
        )


@transactions_app.command("transfer")
def transfer_between_accounts(
    from_account: str = typer.Option(
        ...,
        "--from-account",
        help="Source account (name or ID)",
    ),
    to_account: str = typer.Option(
        ...,
        "--to-account",
        help="Destination account (name or ID)",
    ),
    amount: float = typer.Option(
        ...,
        "--amount",
        help="Transfer amount in dollars (positive number)",
    ),
    date: str = typer.Option(
        ...,
        "--date",
        help="Transfer date (YYYY-MM-DD)",
    ),
    memo: str | None = typer.Option(
        None,
        "--memo",
        help="Transfer memo",
    ),
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
) -> None:
    """
    Create a transfer between two accounts.

    Transfers are special transactions that move money between accounts.
    YNAB automatically creates matching transactions in both accounts.

    Examples:
        # Transfer from Checking to Savings
        ynab transactions transfer --from-account Checking --to-account Savings \\
            --amount 100.00 --date 2024-01-15

        # Transfer with memo
        ynab transactions transfer --from-account "Checking" --to-account "Savings" \\
            --amount 500.00 --date 2024-01-20 --memo "Monthly savings"
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Fetch accounts to get IDs and transfer payee IDs
        accounts_response = asyncio.run(_get_accounts_async(budget_id=budget))
        accounts = accounts_response["data"]["accounts"]

        # Find source and destination accounts
        source_account = None
        dest_account = None

        for account in accounts:
            # Match by name or ID
            if account["name"] == from_account or account["id"] == from_account:
                source_account = account
            if account["name"] == to_account or account["id"] == to_account:
                dest_account = account

        # Validate accounts were found
        if not source_account:
            console.print(f"[red]Error: Source account '{from_account}' not found[/red]")
            raise typer.Exit(1) from None

        if not dest_account:
            console.print(f"[red]Error: Destination account '{to_account}' not found[/red]")
            raise typer.Exit(1) from None

        # Build transfer transaction
        # Amount is negative (leaving source account)
        # Use destination account's transfer_payee_id
        transaction = {
            "account_id": source_account["id"],
            "date": date,
            "amount": -abs(dollars_to_milliunits(amount)),  # Always negative
            "payee_id": dest_account["transfer_payee_id"],
        }

        if memo:
            transaction["memo"] = memo

        # Create transaction (YNAB creates matching transaction automatically)
        response = asyncio.run(
            _create_transaction_async(
                budget_id=budget,
                transaction=transaction,
            )
        )

        created = response["data"]["transaction"]

        console.print("[green]✓ Transfer created successfully[/green]")
        console.print(f"From: {source_account['name']}")
        console.print(f"To: {dest_account['name']}")
        console.print(f"Amount: ${abs(amount):,.2f}")
        console.print(f"Transaction ID: {created['id']}")

    except typer.Exit:
        raise
    except Exception as e:
        handle_cli_error(e)
        raise typer.Exit(1) from None


async def _get_accounts_async(budget_id: str | None) -> dict[str, Any]:
    """Async helper to fetch accounts."""
    async with YNABClient() as client:
        return await client.get_accounts(budget_id=budget_id)
