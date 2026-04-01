"""Category commands for the YNAB CLI."""

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
from ynab_cli.utils import (
    GOAL_TYPE_NAMES,
    convert_monetary_fields,
    dollars_to_milliunits,
    milliunits_to_dollars,
)

categories_app = typer.Typer(
    name="categories",
    help="Manage categories",
    no_args_is_help=True,
)

console = Console()


@categories_app.command("list")
def list_categories(
    budget: str | None = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    show_goals: bool = typer.Option(
        False,
        "--show-goals",
        help="Show goal details",
    ),
    table_output: bool = typer.Option(
        False,
        "--table",
        help="Output as table (default is JSON)",
    ),
) -> None:
    """
    List categories grouped by category groups.

    Shows budgeted, activity, and balance for each category.
    Amounts are displayed in dollars (converted from milliunits).
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        # Run async operation
        response = asyncio.run(_list_categories_async(budget))

        # Extract category groups from response
        category_groups = response["data"]["category_groups"]

        # Output
        if table_output:
            # Table output with hierarchy
            _print_categories_grouped(category_groups, show_goals)
        else:
            # JSON output (default) - convert milliunits to dollars
            output = convert_monetary_fields({"category_groups": category_groups})
            print(json.dumps(output, indent=2))

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


async def _list_categories_async(budget_id: str | None) -> dict[str, Any]:
    """Async helper to fetch categories."""
    async with YNABClient() as client:
        return await client.get_categories(budget_id=budget_id)


@categories_app.command("budget")
def budget_category(
    category_id: str = typer.Argument(
        ...,
        help="Category ID to assign budget amount",
    ),
    month: str = typer.Option(
        ...,
        "--month",
        help="Month in YYYY-MM-01 format (e.g., 2026-04-01)",
    ),
    amount: float = typer.Option(
        ...,
        "--amount",
        help="Amount to assign in dollars (e.g., 250.00)",
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
    Set the budgeted amount for a category in a specific month.

    Assigns money to a category for a given month. The amount is in dollars
    and will be converted to milliunits for the API.

    Examples:
        # Assign $250 to a category for April 2026
        ynab categories budget cat-123 --month 2026-04-01 --amount 250.00

        # Assign $0 to clear a category's budget
        ynab categories budget cat-123 --month 2026-04-01 --amount 0
    """
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1) from None

    try:
        amount_milliunits = dollars_to_milliunits(amount)

        response = asyncio.run(
            _budget_category_async(
                category_id=category_id,
                month=month,
                budgeted=amount_milliunits,
                budget_id=budget,
            )
        )

        updated = response["data"]["category"]

        if table_output:
            console.print("[green]✓ Category budget updated successfully[/green]")
            console.print(f"Category: {updated.get('name', category_id)}")
            console.print(f"Month: {month}")
            console.print(f"Budgeted: ${milliunits_to_dollars(updated.get('budgeted', 0)):,.2f}")
            console.print(f"Balance: ${milliunits_to_dollars(updated.get('balance', 0)):,.2f}")
        else:
            output = convert_monetary_fields({"category": updated})
            print(json.dumps(output, indent=2))

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


async def _budget_category_async(
    category_id: str,
    month: str,
    budgeted: int,
    budget_id: str | None,
) -> dict[str, Any]:
    """Async helper to update category budgeted amount for a month."""
    async with YNABClient() as client:
        return await client.update_category_month(
            category_id=category_id,
            month=month,
            budget_id=budget_id,
            budgeted=budgeted,
        )


def _print_categories_grouped(category_groups: list, show_goals: bool) -> None:
    """Print categories grouped by category groups."""
    for group in category_groups:
        # Skip hidden or deleted groups
        if group.get("hidden") or group.get("deleted"):
            continue

        # Print category group header
        console.print(f"\n[bold cyan]{group['name']}[/bold cyan]")

        # Create table for categories in this group
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Category", style="green")
        table.add_column("Budgeted", style="yellow", justify="right")
        table.add_column("Activity", style="blue", justify="right")
        table.add_column("Balance", style="magenta", justify="right")

        if show_goals:
            table.add_column("Goal", style="cyan")

        # Add categories
        for category in group.get("categories", []):
            # Skip hidden or deleted categories
            if category.get("hidden") or category.get("deleted"):
                continue

            # Convert milliunits to dollars
            budgeted = milliunits_to_dollars(category.get("budgeted", 0))
            activity = milliunits_to_dollars(category.get("activity", 0))
            balance = milliunits_to_dollars(category.get("balance", 0))

            # Format as currency
            budgeted_str = f"${budgeted:,.2f}"
            activity_str = f"${activity:,.2f}"
            balance_str = f"${balance:,.2f}"

            row = [
                category["name"],
                budgeted_str,
                activity_str,
                balance_str,
            ]

            # Add goal info if requested
            if show_goals:
                goal_type = category.get("goal_type")
                if goal_type:
                    goal_target = milliunits_to_dollars(category.get("goal_target", 0))
                    goal_name = GOAL_TYPE_NAMES.get(goal_type, goal_type)
                    goal_str = f"{goal_name}: ${goal_target:,.2f}"
                else:
                    goal_str = ""
                row.append(goal_str)

            table.add_row(*row)

        console.print(table)
