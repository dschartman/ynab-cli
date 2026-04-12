"""Utility functions for YNAB CLI."""

import re
from typing import Any

# All ASCII control characters (0x00-0x1f) are stripped from API string values.
# Although json.dumps escapes \t, \n, and \r, keeping raw control characters in
# Python string values is fragile: any code path that bypasses json.dumps would
# produce invalid JSON.  Stripping them all is the safest defensive approach.
_INVALID_JSON_CONTROL_RE = re.compile(r"[\x00-\x1f]")

# Goal type display names
GOAL_TYPE_NAMES: dict[str, str] = {
    "MF": "Monthly Funding",
    "NEED": "Plan Your Spending",
    "TBD": "Target by Date",
    "TB": "Target Balance",
    "DEBT": "Debt Payoff",
}

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
    Remove all ASCII control characters (0x00-0x1f) from a string.

    The YNAB API can return strings (e.g., category notes) containing raw control
    characters.  Although json.dumps() escapes \\t, \\n, and \\r, keeping them as
    raw characters in Python string values is fragile — any code path that does not
    go through json.dumps() would produce invalid JSON.  Stripping all control
    characters defensively avoids this class of bug entirely.

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
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key in MONETARY_FIELDS and isinstance(value, int):
                result[key] = milliunits_to_dollars(value)
            else:
                result[key] = convert_monetary_fields(value)
        # Enrich goal_type with human-readable name
        goal_type = data.get("goal_type")
        if isinstance(goal_type, str) and goal_type in GOAL_TYPE_NAMES:
            result["goal_type_name"] = GOAL_TYPE_NAMES[goal_type]
        return result
    elif isinstance(data, list):
        return [convert_monetary_fields(item) for item in data]
    elif isinstance(data, str):
        return sanitize_string(value=data)
    else:
        return data
