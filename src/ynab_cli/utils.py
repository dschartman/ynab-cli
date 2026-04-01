"""Utility functions for YNAB CLI."""

import re
from typing import Any

# Control characters that are invalid in JSON (except \t, \n, \r which json.dumps handles)
_INVALID_JSON_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Fields that contain monetary values in milliunits
MONETARY_FIELDS = {
    "balance",
    "cleared_balance",
    "uncleared_balance",
    "budgeted",
    "activity",
    "amount",
    "income",
    "to_be_budgeted",
    "goal_target",
    "goal_under_funded",
    "goal_overall_funded",
    "goal_overall_left",
    "debt_original_balance",
}


def milliunits_to_dollars(amount: int) -> float:
    """
    Convert YNAB milliunits to dollars.

    YNAB stores all monetary amounts as integers in "milliunits":
    - $1.00 = 1000
    - $-12.45 = -12450

    Args:
        amount: Amount in milliunits

    Returns:
        Amount in dollars as a float
    """
    return amount / 1000.0


def dollars_to_milliunits(amount: float) -> int:
    """
    Convert dollars to YNAB milliunits.

    Args:
        amount: Amount in dollars (can be negative for expenses)

    Returns:
        Amount in milliunits as an integer
    """
    return int(amount * 1000)


def sanitize_string(value: str) -> str:
    """
    Remove invalid JSON control characters from a string.

    The YNAB API can return strings (e.g., category notes) containing raw control
    characters that produce invalid JSON when serialized. This replaces problematic
    control characters while preserving tabs, newlines, and carriage returns which
    json.dumps() handles correctly via escaping.

    Args:
        value: String potentially containing control characters

    Returns:
        Sanitized string safe for JSON serialization
    """
    return _INVALID_JSON_CONTROL_RE.sub("", value)


def convert_monetary_fields(data: Any) -> Any:
    """
    Recursively process API response data for JSON output.

    - Converts monetary fields from milliunits (int) to dollars (float)
    - Sanitizes strings to remove invalid JSON control characters

    Args:
        data: API response data (dict, list, or primitive)

    Returns:
        Data with monetary fields converted and strings sanitized
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in MONETARY_FIELDS and isinstance(value, int):
                result[key] = milliunits_to_dollars(value)
            else:
                result[key] = convert_monetary_fields(value)
        return result
    elif isinstance(data, list):
        return [convert_monetary_fields(item) for item in data]
    elif isinstance(data, str):
        return sanitize_string(value=data)
    else:
        return data
