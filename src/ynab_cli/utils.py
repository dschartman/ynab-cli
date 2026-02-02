"""Utility functions for YNAB CLI."""


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
