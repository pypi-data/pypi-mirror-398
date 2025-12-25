"""Custom exception classes for RealtimeX utilities."""

from typing import Any


class RealtimeXError(Exception):
    """Base exception for all RealtimeX errors."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        return self.args[0] if self.args else ""

    def __str__(self) -> str:  # pragma: no cover - default formatting
        return self.message or super().__str__()


class ApiError(RealtimeXError):
    """Raised when API communication fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

    def __str__(self) -> str:
        message = self.message or "API error"
        if self.status_code is not None:
            return f"{message} | Status: {self.status_code}"
        return message


class ConnectionError(ApiError):
    """Raised when network connection fails."""

    pass


class ResourceNotFoundError(ApiError):
    """Raised when a requested resource cannot be located (HTTP 404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: int | None = 404,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)


class AuthenticationError(ApiError):
    """Raised when API authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)


class RateLimitError(ApiError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int | None = None,
        response_body: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)
        self.retry_after = retry_after


class ServerError(ApiError):
    """Raised when server returns 5xx error."""

    def __init__(
        self,
        message: str = "Server error",
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)


class CredentialError(RealtimeXError):
    """Raised when credential retrieval or decryption fails."""

    def __init__(
        self,
        message: str,
        *,
        credential_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.credential_id = credential_id
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        base = self.message or "Credential error"
        extras: list[str] = []
        if self.credential_id:
            extras.append(f"id={self.credential_id}")
        if self.details:
            extras.append(f"details={self.details}")
        if extras:
            return f"{base} ({', '.join(extras)})"
        return base


class ProviderError(RealtimeXError):
    """Raised when LLM provider configuration fails."""

    pass
