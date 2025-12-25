"""Credential-related models and data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CredentialType(StrEnum):
    """Supported credential record types."""

    HTTP_HEADER = "http_header"
    QUERY_AUTH = "query_auth"
    BASIC_AUTH = "basic_auth"
    ENV_VAR = "env_var"


@dataclass(slots=True)
class CredentialBundle:
    """Decrypted credential payload ready for application consumption."""

    credential_id: str
    name: str
    credential_type: CredentialType
    payload: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None
    updated_at: str | None = None

    def as_dict(self) -> dict[str, str]:
        """Return a shallow copy of the secret payload."""
        return dict(self.payload)

    def masked_payload(self) -> dict[str, str]:
        """Return a masked view for safe logging."""
        return dict.fromkeys(self.payload, "[MASKED]")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the bundle into a JSON-friendly structure."""
        return {
            "credential_id": self.credential_id,
            "name": self.name,
            "credential_type": self.credential_type.value,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata) if isinstance(self.metadata, dict) else self.metadata,
            "updated_at": self.updated_at,
        }
