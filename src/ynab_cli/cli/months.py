"""Month commands for the YNAB CLI."""

import asyncio
import json
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from ..api.client import YNABClient
from ..config import settings
from ..error_handling import (
    YNABAPIError,
    YNABAuthenticationError,
    YNABNetworkError,
    format_api_error,
)
from ..utils import milliunits_to_dollars

months_app = typer.Typer(
    name="months",
    help="View budget months",
    no_args_is_help=True,
)

console = Console()


@months_app.command("get")
def get_month(
    month: str = typer.Argument(
        "current",
        help="Month in YYYY-MM-01 format or 'current'",
    ),
    budget: Optional[str] = typer.Option(
        None,
        "--budget",
        help="Budget ID (overrides default)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
):
    """
    Get budget month details with category breakdown.

    Shows income, budgeted amounts, activity, and To Be Budgeted for a specific month.
    Includes detailed breakdown of all categories.

    Examples:
        # Get current month
        ynab months get

        # Get specific month
        ynab months get 2024-01-01

        # Get with JSON output
        ynab months get current --json
    """
    # Check if token is configured
    if not settings or not settings.api_token:
        console.print("[red]Error: API token not configured[/red]")
        console.print("Run 'ynab login' to configure your API token")
        raise typer.Exit(1)

    try:
        # Run async operation
        response = asyncio.run(_get_month_async(
            month=month,
            budget_id=budget,
        ))

        # Extract month data
        month_data = response["data"]["month"]

        # Output
        if json_output:
            console.print(json.dumps({"month": month_data}, indent=2))
        else:
            _print_month_summary(month_data)

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


async def _get_month_async(month: str, budget_id: Optional[str]):
    """Async helper to fetch month details."""
    async with YNABClient() as client:
        return await client.get_month(
            month=month,
            budget_id=budget_id,
        )


def _print_month_summary(month_data: dict):
    """Print month summary in human-readable format."""
    # Header
    console.print(f"\n[bold cyan]Budget Month: {month_data['month']}[/bold cyan]\n")

    # Summary table
    summary_table = Table(title="Month Summary", show_header=False)
    summary_table.add_column("Label", style="cyan")
    summary_table.add_column("Amount", style="yellow", justify="right")

    # Add summary rows
    summary_table.add_row(
        "Income",
        f"${milliunits_to_dollars(month_data.get('income', 0)):,.2f}"
    )
    summary_table.add_row(
        "Budgeted",
        f"${milliunits_to_dollars(month_data.get('budgeted', 0)):,.2f}"
    )

    activity = month_data.get('activity', 0)
    activity_str = f"${milliunits_to_dollars(abs(activity)):,.2f}"
    if activity < 0:
        activity_str = f"-{activity_str}"
    summary_table.add_row("Activity", activity_str)

    summary_table.add_row(
        "To Be Budgeted",
        f"${milliunits_to_dollars(month_data.get('to_be_budgeted', 0)):,.2f}"
    )

    if 'age_of_money' in month_data:
        summary_table.add_row(
            "Age of Money",
            f"{month_data['age_of_money']} days"
        )

    console.print(summary_table)

    # Categories table
    categories = month_data.get('categories', [])
    if categories:
        console.print("\n[bold]Categories:[/bold]\n")

        cat_table = Table()
        cat_table.add_column("Category", style="green")
        cat_table.add_column("Budgeted", style="cyan", justify="right")
        cat_table.add_column("Activity", style="yellow", justify="right")
        cat_table.add_column("Balance", style="magenta", justify="right")

        for category in categories:
            # Skip hidden categories
            if category.get('hidden', False):
                continue

            name = category.get('name', 'Unknown')
            budgeted = milliunits_to_dollars(category.get('budgeted', 0))
            activity = category.get('activity', 0)
            balance = milliunits_to_dollars(category.get('balance', 0))

            # Format activity (usually negative)
            activity_dollars = milliunits_to_dollars(abs(activity))
            activity_str = f"${activity_dollars:,.2f}"
            if activity < 0:
                activity_str = f"-{activity_str}"

            cat_table.add_row(
                name,
                f"${budgeted:,.2f}",
                activity_str,
                f"${balance:,.2f}"
            )

        console.print(cat_table)
        console.print()
