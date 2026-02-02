"""
Tests for CLI entry point (cli/main.py).
"""

import pytest
from ynab_cli.cli.main import app
from ynab_cli import __version__


def test_cli_help(cli_runner):
    """Test that --help flag shows help message."""
    result = cli_runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "YNAB CLI" in result.stdout
    assert "--version" in result.stdout


def test_cli_version_flag(cli_runner):
    """Test that --version flag shows version."""
    result = cli_runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
    assert "ynab-cli version" in result.stdout


def test_cli_version_short_flag(cli_runner):
    """Test that -v short flag shows version."""
    result = cli_runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_no_args_shows_help(cli_runner):
    """Test that running with no arguments shows help (no_args_is_help=True)."""
    result = cli_runner.invoke(app, [])

    # When no args provided, Typer shows help and exits with code 2
    assert result.exit_code == 2
    assert "YNAB CLI" in result.stdout
