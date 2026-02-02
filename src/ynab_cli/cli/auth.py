"""
Authentication commands for YNAB CLI.

Handles login/logout and credential management.
"""

import asyncio
import sys

import httpx
import typer

from ..api.client import YNABClient
from ..config import settings
from ..error_handling import (
    YNABAPIError,
    YNABAuthenticationError,
    YNABNetworkError,
    format_api_error,
)

# Create auth app (not a subgroup - login is a top-level command)
auth_app = typer.Typer(help="Authentication commands")


@auth_app.command(name="login")
def login(
    token: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        help="YNAB API token from https://app.ynab.com/settings/developer"
    ),
    budget_id: str = typer.Option(
        "last-used",
        prompt="Budget ID (or 'last-used', 'default')",
        help="Budget ID to use by default"
    )
):
    """
    Configure YNAB API credentials.

    Get your API token from: https://app.ynab.com/settings/developer

    This command will:
    1. Validate your token with the YNAB API
    2. Save credentials to ~/.config/ynab/config.toml
    3. Set secure file permissions (600)

    Examples:
        ynab login
        ynab login --token YOUR_TOKEN --budget-id last-used
    """
    # Validate token by making a test API call
    typer.echo("Validating API token...")

    try:
        # Run async validation
        user_data = asyncio.run(validate_token(token))

        # Extract user ID from response
        user_id = user_data.get("data", {}).get("user", {}).get("id")

        if not user_id:
            typer.secho(
                "Error: Unable to retrieve user information from YNAB API",
                fg=typer.colors.RED,
                err=True
            )
            raise typer.Exit(1)

        # Token is valid - save credentials
        settings.save_token(token, budget_id)

        # Show success message
        typer.secho("✓ Success!", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"Authenticated as user: {user_id}")
        typer.echo(f"Budget ID: {budget_id}")
        typer.echo(f"\nCredentials saved to: {settings.config_file}")
        typer.echo("\nYou can now use other ynab commands:")
        typer.echo("  ynab budgets list")
        typer.echo("  ynab accounts list")
        typer.echo("  ynab transactions list")

    except YNABAuthenticationError as e:
        typer.secho("Authentication Failed", fg=typer.colors.RED, err=True)
        typer.echo(f"Details: {e.message}", err=True)
        typer.echo("\nThe API token you provided is invalid or expired.")
        typer.echo("Get a new token from: https://app.ynab.com/settings/developer")
        raise typer.Exit(1)
    except YNABNetworkError as e:
        typer.secho("Network Error", fg=typer.colors.RED, err=True)
        typer.echo(f"Details: {e.message}", err=True)
        typer.echo("\nPlease check your internet connection and try again.")
        raise typer.Exit(1)
    except YNABAPIError as e:
        typer.secho("API Error", fg=typer.colors.RED, err=True)
        typer.echo(f"Details: {e.message}", err=True)
        if e.status_code:
            typer.echo(f"Status code: {e.status_code}")
        raise typer.Exit(1)
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        # Convert to specific YNAB error
        ynab_error = format_api_error(e)
        typer.secho("Error", fg=typer.colors.RED, err=True)
        typer.echo(f"Details: {ynab_error}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho("Unexpected Error", fg=typer.colors.RED, err=True)
        typer.echo(f"Details: {str(e)}", err=True)
        typer.echo("\nPlease check:")
        typer.echo("  1. Token is correct (get it from https://app.ynab.com/settings/developer)")
        typer.echo("  2. You have internet connection")
        typer.echo("  3. YNAB API is accessible")
        raise typer.Exit(1)


async def validate_token(token: str) -> dict:
    """
    Validate API token by making a test call to get user info.

    Args:
        token: YNAB API token to validate

    Returns:
        User data from API

    Raises:
        Exception: If token is invalid or API call fails
    """
    async with YNABClient(api_token=token, require_budget=False) as client:
        return await client.get_user()
