"""Utility functions for YNAB CLI."""

from typing import Any


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


def convert_monetary_fields(data: Any) -> Any:
    """
    Recursively convert monetary fields from milliunits to dollars.

    Traverses dicts and lists, converting any field in MONETARY_FIELDS
    from milliunits (int) to dollars (float).

    Args:
        data: API response data (dict, list, or primitive)

    Returns:
        Data with monetary fields converted to dollars
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
    else:
        return data
