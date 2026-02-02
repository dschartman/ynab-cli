"""Tests for context module."""

from ynab_cli.context import is_debug, set_debug


class TestDebugContext:
    """Tests for debug context management."""

    def test_debug_defaults_to_false(self):
        """Debug mode should default to False."""
        # Reset to default
        set_debug(False)
        assert is_debug() is False

    def test_set_debug_enables_debug_mode(self):
        """set_debug(True) should enable debug mode."""
        set_debug(True)
        assert is_debug() is True

        # Clean up
        set_debug(False)

    def test_set_debug_disables_debug_mode(self):
        """set_debug(False) should disable debug mode."""
        set_debug(True)
        set_debug(False)
        assert is_debug() is False

    def test_debug_state_persists(self):
        """Debug state should persist across multiple is_debug() calls."""
        set_debug(True)
        assert is_debug() is True
        assert is_debug() is True

        set_debug(False)
        assert is_debug() is False
        assert is_debug() is False
