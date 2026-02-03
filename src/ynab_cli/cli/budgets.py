"""Budget commands for the YNAB CLI."""

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

budgets_app = typer.Typer(
    name="budgets",
    help="Manage budgets",
    no_args_is_help=True,
)

console = Console()


@budgets_app.command("list")
def list_budgets(
    include_accounts: bool = typer.Option(
        False,
        "--include-accounts",
        help="Include account details for each budget",
    ),
    table_output: bool = typer.Option(
        False,
        "--table",
        help="Output as table (default is JSON)",
    ),
) -> None:
    """
    List all budgets.

    Shows all budgets the authenticated user has access to.
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Run async operation
        response = asyncio.run(_list_budgets_async(include_accounts))

        # Extract budgets from response
        budgets = response["data"]["budgets"]

        # Output
        if table_output:
            # Table output
            _print_budgets_table(budgets, include_accounts)
        else:
            # JSON output (default)
            output = {"budgets": budgets}
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


async def _list_budgets_async(include_accounts: bool) -> dict[str, Any]:
    """Async helper to fetch budgets."""
    async with YNABClient() as client:
        return await client.get_budgets(include_accounts=include_accounts)


def _print_budgets_table(budgets: list, include_accounts: bool) -> None:
    """Print budgets in table format."""
    table = Table(title="Budgets")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Currency", style="yellow")

    if include_accounts:
        table.add_column("Accounts", style="blue")

    for budget in budgets:
        currency_code = budget.get("currency_format", {}).get("iso_code", "N/A")

        row = [
            budget["id"],
            budget["name"],
            currency_code,
        ]

        if include_accounts:
            accounts = budget.get("accounts", [])
            account_count = len(accounts)
            if account_count == 1:
                row.append("1 account")
            else:
                row.append(f"{account_count} accounts")

        table.add_row(*row)

    console.print(table)
