"""Category commands for the YNAB CLI."""

import asyncio
import json
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..api.client import YNABClient
from ..config import settings
from ..error_handling import (
    YNABAPIError,
    YNABAuthenticationError,
    YNABNetworkError,
    format_api_error,
)
from ..utils import milliunits_to_dollars

categories_app = typer.Typer(
    name="categories",
    help="Manage categories",
    no_args_is_help=True,
)

console = Console()


# Goal type display names
GOAL_TYPE_NAMES = {
    "MF": "Monthly Funding",
    "NEED": "Plan Your Spending",
    "TBD": "Target by Date",
    "TB": "Target Balance",
    "DEBT": "Debt Payoff",
}


@categories_app.command("list")
def list_categories(
    budget: Optional[str] = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    show_goals: bool = typer.Option(
        False,
        "--show-goals",
        help="Show goal details",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
):
    """
    List categories grouped by category groups.

    Shows budgeted, activity, and balance for each category.
    Amounts are displayed in dollars (converted from milliunits).
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1)

    try:
        # Run async operation
        response = asyncio.run(_list_categories_async(budget))

        # Extract category groups from response
        category_groups = response["data"]["category_groups"]

        # Output
        if json_output:
            # JSON output
            output = {"category_groups": category_groups}
            console.print(json.dumps(output, indent=2))
        else:
            # Table output with hierarchy
            _print_categories_grouped(category_groups, show_goals)

    except YNABAuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e.message}")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1)
    except YNABNetworkError as e:
        console.print(f"[red]Network Error:[/red] {e.message}")
        raise typer.Exit(1)
    except YNABAPIError as e:
        console.print(f"[red]API Error:[/red] {e.message}")
        if e.status_code:
            console.print(f"Status code: {e.status_code}")
        raise typer.Exit(1)
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        # Convert to specific YNAB error
        ynab_error = format_api_error(e)
        console.print(f"[red]Error:[/red] {ynab_error}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {str(e)}")
        raise typer.Exit(1)


async def _list_categories_async(budget_id: Optional[str]):
    """Async helper to fetch categories."""
    async with YNABClient() as client:
        return await client.get_categories(budget_id=budget_id)


def _print_categories_grouped(category_groups: list, show_goals: bool):
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
