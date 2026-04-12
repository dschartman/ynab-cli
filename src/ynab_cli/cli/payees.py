"""Payee commands for the YNAB CLI."""

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

payees_app = typer.Typer(
    name="payees",
    help="Manage payees",
    no_args_is_help=True,
)

console = Console()


@payees_app.command("list")
def list_payees(
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    search: str | None = typer.Option(
        None,
        "--search",
        help="Filter payees by name (case-insensitive substring match)",
    ),
    table_output: bool = typer.Option(
        False,
        "--table",
        help="Output as table (default is JSON)",
    ),
) -> None:
    """
    List payees for a budget.

    Shows all payees with their IDs. Use --search to filter by name,
    which is useful for looking up payee IDs for transaction commands.

    Examples:
        # List all payees
        ynab payees list

        # Search for a payee by name
        ynab payees list --search "Venmo"

        # Search with table output
        ynab payees list --search "Amazon" --table
    """
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        response = asyncio.run(_list_payees_async(budget))

        payees = response["data"]["payees"]

        # Apply search filter
        if search:
            search_lower = search.lower()
            payees = [p for p in payees if search_lower in (p.get("name") or "").lower()]

        if table_output:
            _print_payees_table(payees, search)
        else:
            print(json.dumps({"payees": payees}, indent=2))

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
        ynab_error = format_api_error(e)
        console.print(f"[red]Error:[/red] {ynab_error}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e!s}")
        raise typer.Exit(1) from None


async def _list_payees_async(budget_id: str | None) -> dict[str, Any]:
    """Async helper to fetch payees."""
    async with YNABClient() as client:
        return await client.get_payees(budget_id=budget_id)


def _print_payees_table(payees: list[dict[str, Any]], search: str | None) -> None:
    """Print payees in table format."""
    title = "Payees"
    if search:
        title = f"Payees matching '{search}'"

    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")

    for payee in payees:
        if payee.get("deleted"):
            continue
        table.add_row(payee["id"], payee.get("name", ""))

    console.print(table)
    console.print(f"\n{len(payees)} payee(s) found")
