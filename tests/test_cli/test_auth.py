"""
Tests for authentication commands (login/logout).
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from ynab_cli.cli.main import app


@pytest.fixture
def runner():
    """Fixture providing a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Fixture providing a temporary config directory."""
    config_dir = tmp_path / ".config" / "ynab"
    config_dir.mkdir(parents=True)

    # Mock Path.home() to return tmp_path
    def mock_home():
        return tmp_path

    monkeypatch.setattr(Path, "home", mock_home)
    return config_dir


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture that clears YNAB-related environment variables."""
    monkeypatch.delenv("YNAB_API_TOKEN", raising=False)
    monkeypatch.delenv("YNAB_BUDGET_ID", raising=False)


class TestLoginCommand:
    """Test 'ynab login' command."""

    def test_login_with_valid_token(self, runner, temp_config_dir, clean_env):
        """Test login command with valid API token."""
        # Mock the YNAB API client
        mock_user_response = {
            "data": {
                "user": {
                    "id": "user-123"
                }
            }
        }

        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            # Setup mock client instance
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(return_value=mock_user_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            # Run command with token input
            result = runner.invoke(
                app,
                ["login"],
                input="test-token-123\nlast-used\n"
            )

            assert result.exit_code == 0
            assert "Success" in result.stdout or "success" in result.stdout
            assert "user-123" in result.stdout
            assert str(temp_config_dir / "config.toml") in result.stdout

            # Verify config file was created
            config_file = temp_config_dir / "config.toml"
            assert config_file.exists()
            content = config_file.read_text()
            assert 'api_token = "test-token-123"' in content
            assert 'budget_id = "last-used"' in content

    def test_login_with_custom_budget_id(self, runner, temp_config_dir, clean_env):
        """Test login command with custom budget ID."""
        mock_user_response = {"data": {"user": {"id": "user-456"}}}

        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(return_value=mock_user_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="test-token\ncustom-budget-id\n"
            )

            assert result.exit_code == 0

            # Verify custom budget ID was saved
            config_file = temp_config_dir / "config.toml"
            content = config_file.read_text()
            assert 'budget_id = "custom-budget-id"' in content

    def test_login_with_invalid_token(self, runner, temp_config_dir, clean_env):
        """Test login command with invalid API token."""
        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            # Setup mock to raise an error
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(side_effect=Exception("401 Unauthorized"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="invalid-token\nlast-used\n"
            )

            assert result.exit_code == 1
            # Check both stdout and stderr for error messages
            output = result.stdout + (result.stderr or "")
            assert "Error" in output or "error" in output or "Failed" in output

            # Verify config file was NOT created
            config_file = temp_config_dir / "config.toml"
            assert not config_file.exists()

    def test_login_hides_token_input(self, runner, temp_config_dir, clean_env):
        """Test that token input is hidden in prompt."""
        # Note: This test verifies the command structure, actual hiding
        # is handled by Typer's Option(hide_input=True)
        mock_user_response = {"data": {"user": {"id": "user-789"}}}

        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(return_value=mock_user_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="hidden-token\nlast-used\n"
            )

            assert result.exit_code == 0
            # Token should not be visible in the output
            assert "hidden-token" not in result.stdout

    def test_login_with_network_error(self, runner, temp_config_dir, clean_env):
        """Test login command handles network errors gracefully."""
        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(
                side_effect=Exception("Network connection failed")
            )
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="test-token\nlast-used\n"
            )

            assert result.exit_code == 1
            # Check both stdout and stderr for error messages
            output = result.stdout + (result.stderr or "")
            assert "Error" in output or "error" in output or "Failed" in output

    def test_login_shows_helpful_message(self, runner, temp_config_dir, clean_env):
        """Test that login command shows helpful instructions."""
        mock_user_response = {"data": {"user": {"id": "user-help"}}}

        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(return_value=mock_user_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="test-token\nlast-used\n"
            )

            assert result.exit_code == 0
            # Should mention where credentials are saved
            assert "config" in result.stdout.lower()

    def test_login_validates_before_saving(self, runner, temp_config_dir, clean_env):
        """Test that login validates token before saving to config."""
        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            # Token validation fails
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(side_effect=Exception("Invalid token"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="bad-token\nlast-used\n"
            )

            # Should fail and NOT create config file
            assert result.exit_code == 1
            config_file = temp_config_dir / "config.toml"
            assert not config_file.exists()

    def test_login_overwrites_existing_config(self, runner, temp_config_dir, clean_env):
        """Test that login overwrites existing configuration."""
        # Create existing config
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('api_token = "old-token"\nbudget_id = "old-budget"\n')

        mock_user_response = {"data": {"user": {"id": "new-user"}}}

        with patch("ynab_cli.cli.auth.YNABClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_user = AsyncMock(return_value=mock_user_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = runner.invoke(
                app,
                ["login"],
                input="new-token\nnew-budget\n"
            )

            assert result.exit_code == 0

            # Verify old config was replaced
            content = config_file.read_text()
            assert 'api_token = "new-token"' in content
            assert 'budget_id = "new-budget"' in content
            assert "old-token" not in content
            assert "old-budget" not in content


class TestLoginHelp:
    """Test login command help text."""

    def test_login_help_includes_token_url(self, runner):
        """Test that login help text includes URL to get API token."""
        result = runner.invoke(app, ["login", "--help"])

        assert result.exit_code == 0
        # Should mention where to get the token
        assert "https://app.ynab.com/settings/developer" in result.stdout
