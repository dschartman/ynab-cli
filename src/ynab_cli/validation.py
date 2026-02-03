"""Input validation for CLI commands."""

import re
from datetime import datetime


class ValidationError(ValueError):
    """Exception raised for validation errors."""

    pass


def validate_date(date_str: str) -> str:
    """
    Validate date format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        Validated date string

    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str:
        raise ValidationError("Date cannot be empty")

    # Check format with regex
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValidationError(
            f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD (e.g., 2025-01-15)"
        )

    # Validate actual date values
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValidationError(f"Invalid date: {e!s}") from e

    return date_str


def validate_amount(amount_str: str) -> float:
    """
    Validate monetary amount.

    Args:
        amount_str: Amount string to validate

    Returns:
        Validated amount as float

    Raises:
        ValidationError: If amount format is invalid
    """
    if not amount_str:
        raise ValidationError("Amount cannot be empty")

    # Try to convert to float
    try:
        amount = float(amount_str)
    except ValueError as e:
        raise ValidationError(f"Invalid amount: '{amount_str}'. Must be a valid number.") from e

    # Check decimal places
    if "." in amount_str:
        decimal_part = amount_str.split(".")[1]
        if len(decimal_part) > 2:
            raise ValidationError(
                f"Invalid amount: '{amount_str}'. Amount can have at most two decimal places."
            )

    return amount


def validate_uuid(uuid_str: str) -> str:
    """
    Validate UUID format or special YNAB budget IDs.

    Args:
        uuid_str: UUID string to validate

    Returns:
        Validated UUID string

    Raises:
        ValidationError: If UUID format is invalid
    """
    if not uuid_str:
        raise ValidationError("ID cannot be empty")

    # Allow special YNAB budget ID values
    if uuid_str in ["last-used", "default"]:
        return uuid_str

    # UUID format: 8-4-4-4-12 hex digits
    uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

    if not re.match(uuid_pattern, uuid_str):
        raise ValidationError(
            f"Invalid UUID format: '{uuid_str}'. "
            "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx "
            "or special values: 'last-used', 'default'"
        )

    return uuid_str
