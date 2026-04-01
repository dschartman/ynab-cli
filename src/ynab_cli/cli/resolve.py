"""Name-to-ID resolution helpers for CLI commands."""

import asyncio
from typing import Any

from ynab_cli.api.client import YNABClient


def resolve_category_name(name: str, budget_id: str | None = None) -> str:
    """
    Resolve a category name to its ID.

    Fetches all categories, searches for a case-insensitive match.
    Errors if no match or multiple matches found.

    Args:
        name: Category name to look up
        budget_id: Budget ID override

    Returns:
        Category ID string

    Raises:
        ValueError: If no match or ambiguous match
    """
    response = asyncio.run(_get_categories_async(budget_id))
    category_groups = response["data"]["category_groups"]

    matches: list[dict[str, Any]] = []
    name_lower = name.lower()

    for group in category_groups:
        if group.get("hidden") or group.get("deleted"):
            continue
        for cat in group.get("categories", []):
            if cat.get("hidden") or cat.get("deleted"):
                continue
            if cat["name"].lower() == name_lower:
                matches.append(cat)

    if len(matches) == 0:
        raise ValueError(f"Category not found: '{name}'")
    if len(matches) > 1:
        match_list = ", ".join(f"'{m['name']}' ({m['id']})" for m in matches)
        raise ValueError(
            f"Multiple categories match '{name}': {match_list}. Use --category with the ID instead."
        )

    return str(matches[0]["id"])


def resolve_payee_name(name: str, budget_id: str | None = None) -> str:
    """
    Resolve a payee name to its ID.

    Fetches all payees, searches for a case-insensitive match.
    Errors if no match or multiple matches found.

    Args:
        name: Payee name to look up
        budget_id: Budget ID override

    Returns:
        Payee ID string

    Raises:
        ValueError: If no match or ambiguous match
    """
    response = asyncio.run(_get_payees_async(budget_id))
    payees = response["data"]["payees"]

    matches: list[dict[str, Any]] = []
    name_lower = name.lower()

    for payee in payees:
        if payee.get("deleted"):
            continue
        if (payee.get("name") or "").lower() == name_lower:
            matches.append(payee)

    if len(matches) == 0:
        raise ValueError(f"Payee not found: '{name}'")
    if len(matches) > 1:
        match_list = ", ".join(f"'{m['name']}' ({m['id']})" for m in matches)
        raise ValueError(
            f"Multiple payees match '{name}': {match_list}. Use --payee with the ID instead."
        )

    return str(matches[0]["id"])


async def _get_categories_async(budget_id: str | None) -> dict[str, Any]:
    """Async helper to fetch categories."""
    async with YNABClient() as client:
        return await client.get_categories(budget_id=budget_id)


async def _get_payees_async(budget_id: str | None) -> dict[str, Any]:
    """Async helper to fetch payees."""
    async with YNABClient() as client:
        return await client.get_payees(budget_id=budget_id)
