"""Helpers for interacting with the Gmail MCP linked account."""

from __future__ import annotations

from realtimex_toolkit.api.utils import sync_fetch_json
from realtimex_toolkit.exceptions import RealtimeXError
from realtimex_toolkit.utils.path_utils import get_env_value

MCP_BASE_URL = "https://mcp.realtimex.ai"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


def get_gmail_email(
    *,
    linked_account_owner_id: str | None = None,
    api_key: str | None = None,
    base_url: str = MCP_BASE_URL,
) -> str:
    """Retrieve the configured Gmail email address for the MCP server.

    Args:
        linked_account_owner_id: Owner ID for linked account; defaults to env MCP_PROXY_LINKED_ACCOUNT_OWNER_ID.
        api_key: MCP API key; defaults to env MCP_PROXY_API_KEY.
        base_url: MCP base URL (default: https://mcp.realtimex.ai).

    Returns:
        The Gmail email address associated with the linked account.

    Raises:
        ValueError: If required credentials are missing.
        RealtimeXError: If account lookup or token retrieval fails.
        ApiError: For HTTP errors.
    """
    owner_id = linked_account_owner_id or get_env_value("MCP_PROXY_LINKED_ACCOUNT_OWNER_ID")
    key = api_key or get_env_value("MCP_PROXY_API_KEY")

    if not owner_id:
        raise ValueError("MCP_PROXY_LINKED_ACCOUNT_OWNER_ID is required")
    if not key:
        raise ValueError("MCP_PROXY_API_KEY is required")

    mcp_headers = {"X-API-KEY": key}

    # Step 1: list linked accounts for GMAIL
    accounts = sync_fetch_json(
        f"{base_url.rstrip('/')}/v1/linked-accounts",
        mcp_headers,
        {"app_name": "GMAIL", "linked_account_owner_id": owner_id},
    )

    if not accounts:
        raise RealtimeXError("No GMAIL linked accounts found for the provided owner id")

    gmail_account = None
    for account in accounts:
        if isinstance(account, dict) and account.get("app_name") == "GMAIL":
            gmail_account = account
            break

    if not gmail_account:
        raise RealtimeXError("GMAIL linked account not found in MCP response")

    linked_account_id = gmail_account.get("id")
    if not linked_account_id:
        raise RealtimeXError("Linked account id missing from MCP response")

    # Step 2: get account details to retrieve access token
    account_detail = sync_fetch_json(
        f"{base_url.rstrip('/')}/v1/linked-accounts/{linked_account_id}",
        mcp_headers,
        None,
    )

    security_credentials = (
        account_detail.get("security_credentials") if isinstance(account_detail, dict) else None
    )
    access_token = security_credentials.get("access_token") if security_credentials else None

    if not access_token:
        raise RealtimeXError("Access token not found for Gmail linked account")

    # Step 3: call Gmail profile endpoint to get email
    profile = sync_fetch_json(
        GMAIL_PROFILE_URL,
        {"Authorization": f"Bearer {access_token}"},
        None,
    )

    if not isinstance(profile, dict) or "emailAddress" not in profile:
        raise RealtimeXError("Unable to retrieve Gmail email address from profile response")

    return profile["emailAddress"]
