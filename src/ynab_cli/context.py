"""Global context for CLI state."""

# Global debug state
_debug_enabled = False


def set_debug(enabled: bool) -> None:
    """
    Set debug mode.

    Args:
        enabled: Whether debug mode is enabled
    """
    global _debug_enabled
    _debug_enabled = enabled


def is_debug() -> bool:
    """
    Check if debug mode is enabled.

    Returns:
        True if debug mode is enabled
    """
    return _debug_enabled
