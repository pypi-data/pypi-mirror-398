"""Credential management utilities."""

from typing import Any

from realtimex_toolkit.credentials.manager import CredentialManager
from realtimex_toolkit.credentials.models import CredentialBundle, CredentialType


def get_credential(
    credential_id: str,
    *,
    api_key: str = "",
    base_url: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Retrieve and decrypt a credential by ID - convenience wrapper.

    This is a convenience function that creates a CredentialManager instance,
    fetches the credential, and properly closes the connection.

    Args:
        credential_id: The unique identifier for the credential
        api_key: API authentication key (default: empty string)
        base_url: Base URL for the API (default: http://localhost:3001)
        force_refresh: If True, bypass cache and fetch fresh data (default: False)

    Returns:
        Dictionary containing decrypted credential data in a JSON-friendly shape:
        {
            "credential_id": str,
            "name": str,
            "credential_type": str,
            "payload": dict[str, str],
            "metadata": dict | None,
            "updated_at": str | None,
        }

    Raises:
        CredentialError: If credential cannot be retrieved or decrypted

    Example:
        >>> bundle = get_credential("cred-123", api_key="your-api-key")
        >>> print(bundle["payload"])
        {'name': 'API_KEY', 'value': 'secret-value'}
    """
    kwargs = {"api_key": api_key}
    if base_url is not None:
        kwargs["base_url"] = base_url

    manager = CredentialManager(**kwargs)
    try:
        bundle = manager.get(credential_id, force_refresh=force_refresh)
        return bundle.to_dict()
    finally:
        manager.close()


__all__ = [
    "CredentialBundle",
    "CredentialManager",
    "CredentialType",
    "get_credential",
]
