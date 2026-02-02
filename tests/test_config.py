"""
Tests for configuration management (config.py).

Tests config file at ~/.config/ynab/config.toml and environment variables.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ynab_cli.config import Settings


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


class TestSettingsInit:
    """Test Settings initialization and configuration paths."""

    def test_config_paths(self, temp_config_dir):
        """Test that config paths are correctly set."""
        settings = Settings()
        assert settings.config_dir == temp_config_dir
        assert settings.config_file == temp_config_dir / "config.toml"

    def test_config_dir_from_home(self, temp_config_dir):
        """Test config directory is created from user's home directory."""
        settings = Settings()
        # Should be ~/.config/ynab (but with mocked home)
        assert settings.config_dir.name == "ynab"
        assert settings.config_dir.parent.name == ".config"


class TestApiToken:
    """Test api_token property reading from env and config file."""

    def test_token_from_env_var(self, temp_config_dir, monkeypatch):
        """Test api_token reads from YNAB_API_TOKEN environment variable."""
        monkeypatch.setenv("YNAB_API_TOKEN", "env-token-123")
        settings = Settings()
        assert settings.api_token == "env-token-123"

    def test_token_from_config_file(self, temp_config_dir, clean_env):
        """Test api_token reads from config.toml when no env var."""
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('api_token = "file-token-456"\n')

        settings = Settings()
        assert settings.api_token == "file-token-456"

    def test_token_env_var_priority(self, temp_config_dir, monkeypatch):
        """Test env var takes priority over config file."""
        # Create config file with one token
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('api_token = "file-token"\n')

        # Set env var with different token
        monkeypatch.setenv("YNAB_API_TOKEN", "env-token")

        settings = Settings()
        assert settings.api_token == "env-token"

    def test_token_none_when_not_found(self, temp_config_dir, clean_env):
        """Test api_token returns None when not in env or config file."""
        settings = Settings()
        assert settings.api_token is None

    def test_token_none_when_config_file_missing(self, temp_config_dir, clean_env):
        """Test api_token returns None when config file doesn't exist."""
        # Don't create config file
        settings = Settings()
        assert settings.api_token is None


class TestBudgetId:
    """Test budget_id property reading from env and config file."""

    def test_budget_id_from_env_var(self, temp_config_dir, monkeypatch):
        """Test budget_id reads from YNAB_BUDGET_ID environment variable."""
        monkeypatch.setenv("YNAB_BUDGET_ID", "env-budget-123")
        settings = Settings()
        assert settings.budget_id == "env-budget-123"

    def test_budget_id_from_config_file(self, temp_config_dir, clean_env):
        """Test budget_id reads from config.toml when no env var."""
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('budget_id = "file-budget-456"\n')

        settings = Settings()
        assert settings.budget_id == "file-budget-456"

    def test_budget_id_env_var_priority(self, temp_config_dir, monkeypatch):
        """Test env var takes priority over config file."""
        # Create config file
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('budget_id = "file-budget"\n')

        # Set env var
        monkeypatch.setenv("YNAB_BUDGET_ID", "env-budget")

        settings = Settings()
        assert settings.budget_id == "env-budget"

    def test_budget_id_defaults_to_last_used(self, temp_config_dir, clean_env):
        """Test budget_id defaults to 'last-used' when not found."""
        settings = Settings()
        assert settings.budget_id == "last-used"


class TestSaveToken:
    """Test save_token method for persisting credentials."""

    def test_save_token_creates_config_file(self, temp_config_dir, clean_env):
        """Test save_token creates config file with token and budget_id."""
        settings = Settings()
        settings.save_token("new-token", "new-budget")

        config_file = temp_config_dir / "config.toml"
        assert config_file.exists()

        content = config_file.read_text()
        assert 'api_token = "new-token"' in content
        assert 'budget_id = "new-budget"' in content

    def test_save_token_creates_directory_if_missing(self, tmp_path, monkeypatch, clean_env):
        """Test save_token creates config directory if it doesn't exist."""
        # Mock home to tmp_path but don't create the .config/ynab directory
        def mock_home():
            return tmp_path
        monkeypatch.setattr(Path, "home", mock_home)

        settings = Settings()
        settings.save_token("test-token", "test-budget")

        config_dir = tmp_path / ".config" / "ynab"
        assert config_dir.exists()
        assert (config_dir / "config.toml").exists()

    def test_save_token_sets_secure_permissions(self, temp_config_dir, clean_env):
        """Test save_token sets file permissions to 0o600 (user read/write only)."""
        settings = Settings()
        settings.save_token("secure-token", "secure-budget")

        config_file = temp_config_dir / "config.toml"
        # Get file permissions (last 3 octal digits)
        permissions = oct(config_file.stat().st_mode)[-3:]
        assert permissions == "600"

    def test_save_token_overwrites_existing(self, temp_config_dir, clean_env):
        """Test save_token overwrites existing config file."""
        # Create initial config
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('api_token = "old-token"\nbudget_id = "old-budget"\n')

        settings = Settings()
        settings.save_token("new-token", "new-budget")

        content = config_file.read_text()
        assert 'api_token = "new-token"' in content
        assert 'budget_id = "new-budget"' in content
        assert "old-token" not in content
        assert "old-budget" not in content

    def test_save_token_with_default_budget(self, temp_config_dir, clean_env):
        """Test save_token with default budget_id value."""
        settings = Settings()
        settings.save_token("token-123", "last-used")

        config_file = temp_config_dir / "config.toml"
        content = config_file.read_text()
        assert 'api_token = "token-123"' in content
        assert 'budget_id = "last-used"' in content


class TestConfigFileFormat:
    """Test TOML config file format and parsing."""

    def test_reads_valid_toml(self, temp_config_dir, clean_env):
        """Test Settings can read valid TOML format."""
        config_file = temp_config_dir / "config.toml"
        config_file.write_text("""
# YNAB CLI Configuration
api_token = "toml-token"
budget_id = "toml-budget"
""")

        settings = Settings()
        assert settings.api_token == "toml-token"
        assert settings.budget_id == "toml-budget"

    def test_handles_malformed_toml(self, temp_config_dir, clean_env):
        """Test Settings handles malformed TOML gracefully."""
        config_file = temp_config_dir / "config.toml"
        config_file.write_text("this is not valid toml {]}")

        # Should not raise exception, just return None
        settings = Settings()
        assert settings.api_token is None
        assert settings.budget_id == "last-used"

    def test_handles_missing_fields(self, temp_config_dir, clean_env):
        """Test Settings handles TOML with missing fields."""
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('api_token = "only-token"\n')

        settings = Settings()
        assert settings.api_token == "only-token"
        assert settings.budget_id == "last-used"  # Should use default
