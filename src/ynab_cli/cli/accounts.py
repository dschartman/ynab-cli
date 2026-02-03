"""Account commands for the YNAB CLI."""

import asyncio
import json
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

from ynab_cli.api.client import YNABClient
from ynab_cli.config import settings
from ynab_cli.error_handling import (
    YNABAPIError,
    YNABAuthenticationError,
    YNABNetworkError,
    format_api_error,
)
from ynab_cli.utils import convert_monetary_fields, milliunits_to_dollars

accounts_app = typer.Typer(
    name="accounts",
    help="Manage accounts",
    no_args_is_help=True,
)

console = Console()


@accounts_app.command("list")
def list_accounts(
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
    List all accounts for a budget.

    Shows checking, savings, credit cards, loans, and other accounts.
    Balances are displayed in dollars (converted from milliunits).
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Run async operation
        response = asyncio.run(_list_accounts_async(budget))

        # Extract accounts from response
        accounts = response["data"]["accounts"]

        # Output
        if table_output:
            # Table output
            _print_accounts_table(accounts)
        else:
            # JSON output (default) - convert milliunits to dollars
            output = convert_monetary_fields({"accounts": accounts})
            console.print(json.dumps(output, indent=2))

    except YNABAuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e.message}")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None
    except YNABNetworkError as e:
        console.print(f"[red]Network Error:[/red] {e.message}")
        raise typer.Exit(1) from None
    except YNABAPIError as e:
        console.print(f"[red]API Error:[/red] {e.message}")
        if e.status_code:
            console.print(f"Status code: {e.status_code}")
        raise typer.Exit(1) from None
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        # Convert to specific YNAB error
        ynab_error = format_api_error(e)
        console.print(f"[red]Error:[/red] {ynab_error}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e!s}")
        raise typer.Exit(1) from None


async def _list_accounts_async(budget_id: str | None) -> dict[str, Any]:
    """Async helper to fetch accounts."""
    async with YNABClient() as client:
        return await client.get_accounts(budget_id=budget_id)


def _print_accounts_table(accounts: list) -> None:
    """Print accounts in table format."""
    table = Table(title="Accounts")
    table.add_column("Name", style="green")
    table.add_column("Type", style="cyan")
    table.add_column("Balance", style="yellow", justify="right")
    table.add_column("Cleared", style="blue", justify="right")
    table.add_column("Uncleared", style="magenta", justify="right")
    table.add_column("Closed", style="red", justify="center")

    for account in accounts:
        # Convert milliunits to dollars
        balance = milliunits_to_dollars(account["balance"])
        cleared = milliunits_to_dollars(account["cleared_balance"])
        uncleared = milliunits_to_dollars(account["uncleared_balance"])

        # Format as currency
        balance_str = f"${balance:,.2f}"
        cleared_str = f"${cleared:,.2f}"
        uncleared_str = f"${uncleared:,.2f}"

        # Closed status
        closed_str = "✓" if account["closed"] else ""

        table.add_row(
            account["name"],
            account["type"],
            balance_str,
            cleared_str,
            uncleared_str,
            closed_str,
        )

    console.print(table)
