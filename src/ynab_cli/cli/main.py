"""
Main CLI entry point.

Defines the Typer app and command groups for the ynab CLI tool.
"""

import typer

from ..context import set_debug
from ..logging_config import setup_logging
from .accounts import accounts_app
from .auth import login
from .budgets import budgets_app
from .categories import categories_app
from .months import months_app
from .transactions import transactions_app

app = typer.Typer(
    name="ynab",
    help="YNAB CLI - Python CLI for the YNAB API",
    no_args_is_help=True,
)

# Register top-level commands
app.command()(login)

# Register command groups
app.add_typer(accounts_app, name="accounts")
app.add_typer(budgets_app, name="budgets")
app.add_typer(categories_app, name="categories")
app.add_typer(months_app, name="months")
app.add_typer(transactions_app, name="transactions")


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        from ynab_cli import __version__
        typer.echo(f"ynab-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode with verbose error messages and stack traces",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging (API requests/responses)",
    )
):
    """
    YNAB CLI - Comprehensive Python CLI for the YNAB API.

    Designed for programmatic use by Claude Code and automation tools.
    """
    # Set global debug state
    set_debug(debug)

    # Configure logging
    setup_logging(verbose=verbose)


if __name__ == "__main__":
    app()
