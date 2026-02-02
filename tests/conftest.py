"""
Pytest configuration and shared fixtures.
"""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Fixture providing a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_env(monkeypatch):
    """Fixture for setting environment variables in tests."""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
    return _set_env


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture that clears YNAB-related environment variables."""
    monkeypatch.delenv("YNAB_API_TOKEN", raising=False)
    monkeypatch.delenv("YNAB_DEFAULT_BUDGET_ID", raising=False)
