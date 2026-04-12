"""
YNAB API client module.

Handles HTTP communication with the YNAB API including rate limiting and error handling.
"""

from ynab_cli.api.client import YNABClient, get_ynab_client

__all__ = ["YNABClient", "get_ynab_client"]
