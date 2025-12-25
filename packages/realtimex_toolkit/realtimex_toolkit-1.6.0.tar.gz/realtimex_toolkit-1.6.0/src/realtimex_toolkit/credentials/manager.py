"""Credential retrieval and decryption utilities."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import threading
from typing import Any
from urllib.parse import quote

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from realtimex_toolkit.api.http_client import ApiClient
from realtimex_toolkit.credentials.models import CredentialBundle, CredentialType
from realtimex_toolkit.exceptions import ApiError, CredentialError
from realtimex_toolkit.utils.path_utils import get_shared_env_path

try:  # pragma: no cover - optional dependency is always available in prod envs
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover - fallback when python-dotenv not installed
    dotenv_values = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class _EventLoopThread:
    """Background thread with a long-lived event loop for running async operations."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()

    def start(self) -> None:
        """Start the background thread and event loop."""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        self._started.wait()

    def _run_event_loop(self) -> None:
        """Run the event loop in the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._started.set()
        self._loop.run_forever()

    def run_coroutine(self, coro):
        """Schedule a coroutine on the event loop and return the result."""
        if self._loop is None:
            raise RuntimeError("Event loop thread not started")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def stop(self) -> None:
        """Stop the event loop and thread."""
        if self._loop is not None and self._thread is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5.0)
            self._loop.close()
            self._loop = None
            self._thread = None


class CredentialManager:
    """Loads credential records from the RealTimeX app backend and decrypts them for consumption."""

    DEFAULT_BASE_URL = "http://localhost:3001"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str = "",
        *,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """Initialize CredentialManager.

        Args:
            base_url: Base URL for the API (default: http://localhost:3001)
            api_key: API authentication key
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self._loop_thread = _EventLoopThread()
        self._loop_thread.start()
        self._closed = False

        self._api_client = ApiClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._cache: dict[str, CredentialBundle] = {}
        self._cache_lock = threading.Lock()

        key, salt = self._load_key_material()
        self._encryption_key = self._derive_key(key, salt)

    def close(self) -> None:
        """Close the underlying HTTP client session and stop the event loop thread."""
        if self._closed:
            return

        self._closed = True
        try:
            self._loop_thread.run_coroutine(self._api_client.close())
        except RuntimeError:
            # Event loop already torn down - nothing left to close
            pass
        finally:
            with self._cache_lock:
                self._cache.clear()
            self._loop_thread.stop()

    def __enter__(self) -> CredentialManager:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def get(self, credential_id: str, *, force_refresh: bool = False) -> CredentialBundle:
        """Retrieve and decrypt a credential by id.

        Args:
            credential_id: The unique identifier for the credential
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            CredentialBundle containing decrypted credential data

        Raises:
            CredentialError: If credential cannot be retrieved or decrypted
        """
        if self._closed:
            raise CredentialError("Credential manager is closed", credential_id=credential_id)

        if not force_refresh:
            cached = self._cache.get(credential_id)
            if cached is not None:
                return cached

        with self._cache_lock:
            if self._closed:
                raise CredentialError("Credential manager is closed", credential_id=credential_id)

            if not force_refresh:
                cached = self._cache.get(credential_id)
                if cached is not None:
                    return cached

            raw_record = self._loop_thread.run_coroutine(self._fetch_credential(credential_id))
            bundle = self._build_bundle(raw_record)
            self._cache[credential_id] = bundle
            return bundle

    def clear_cache(self) -> None:
        """Evict cached credential bundles."""
        with self._cache_lock:
            self._cache.clear()

    async def _fetch_credential(self, credential_id: str) -> dict[str, Any]:
        try:
            encoded_credential_id = quote(str(credential_id), safe="")
            payload = await self._api_client.request(
                "GET", f"/api/v1/credentials/{encoded_credential_id}"
            )
        except ApiError as exc:  # pragma: no cover - network errors exercised in integration tests
            raise CredentialError(
                f"Failed to fetch credential '{credential_id}' from credential service",
                credential_id=credential_id,
            ) from exc

        if not isinstance(payload, dict):
            raise CredentialError(
                "Credential service returned an unexpected response",
                credential_id=credential_id,
            )

        return self._extract_credential(payload, credential_id)

    def _extract_credential(self, payload: dict[str, Any], credential_id: str) -> dict[str, Any]:
        status = payload.get("status")
        if status is False:
            raise CredentialError(
                "Credential service reported failure",
                credential_id=credential_id,
                details={"status": status},
            )

        credential = payload.get("credential")
        if not isinstance(credential, dict):
            raise CredentialError(
                "Credential service returned malformed credential payload",
                credential_id=credential_id,
            )

        return credential

    def _build_bundle(self, record: dict[str, Any]) -> CredentialBundle:
        credential_id = str(record.get("id", ""))
        raw_type = record.get("type")
        if not raw_type:
            raise CredentialError("Credential record missing type", credential_id=credential_id)

        try:
            credential_type = CredentialType(raw_type)
        except ValueError as exc:
            raise CredentialError(
                f"Unsupported credential type '{raw_type}'",
                credential_id=credential_id,
            ) from exc

        encrypted_blob = record.get("data")
        if not isinstance(encrypted_blob, str) or not encrypted_blob:
            raise CredentialError("Credential record missing payload", credential_id=credential_id)

        decrypted_json = self._decrypt_blob(encrypted_blob, credential_id)
        payload = self._parse_payload(decrypted_json, credential_type, credential_id)

        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else None
        updated_at = record.get("updated_at") if isinstance(record.get("updated_at"), str) else None
        name = str(record.get("name")) if record.get("name") is not None else credential_id

        return CredentialBundle(
            credential_id=credential_id,
            name=name,
            credential_type=credential_type,
            payload=payload,
            metadata=metadata,
            updated_at=updated_at,
        )

    def _decrypt_blob(self, encoded_blob: str, credential_id: str) -> str:
        try:
            encrypted_bytes = base64.b64decode(encoded_blob)
        except ValueError as exc:
            raise CredentialError(
                "Credential payload is not valid base64",
                credential_id=credential_id,
            ) from exc

        try:
            encrypted_text = encrypted_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CredentialError(
                "Credential payload is not UTF-8 encoded",
                credential_id=credential_id,
            ) from exc

        try:
            cipher_hex, iv_hex = encrypted_text.split(":", 1)
        except ValueError as exc:
            raise CredentialError(
                "Credential payload is missing initialization vector",
                credential_id=credential_id,
            ) from exc

        try:
            cipher_bytes = bytes.fromhex(cipher_hex)
            iv_bytes = bytes.fromhex(iv_hex)
        except ValueError as exc:
            raise CredentialError(
                "Credential payload contains invalid hex data",
                credential_id=credential_id,
            ) from exc

        cipher = Cipher(algorithms.AES(self._encryption_key), modes.CBC(iv_bytes))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(cipher_bytes) + decryptor.finalize()

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        try:
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()
        except ValueError as exc:
            raise CredentialError(
                "Credential payload failed padding validation",
                credential_id=credential_id,
            ) from exc

        try:
            return plaintext_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CredentialError(
                "Credential payload could not be decoded",
                credential_id=credential_id,
            ) from exc

    def _parse_payload(
        self,
        payload_json: str,
        credential_type: CredentialType,
        credential_id: str,
    ) -> dict[str, str]:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise CredentialError(
                "Credential payload is not valid JSON",
                credential_id=credential_id,
            ) from exc

        if not isinstance(payload, dict):
            raise CredentialError(
                "Credential payload must be a JSON object",
                credential_id=credential_id,
            )

        if credential_type is CredentialType.BASIC_AUTH:
            username = payload.get("username")
            password = payload.get("password")
            if not isinstance(username, str) or not isinstance(password, str):
                raise CredentialError(
                    "Basic auth credential payload requires username and password",
                    credential_id=credential_id,
                )
            return {"username": username, "password": password}

        if credential_type in {
            CredentialType.HTTP_HEADER,
            CredentialType.QUERY_AUTH,
            CredentialType.ENV_VAR,
        }:
            name = payload.get("name")
            value = payload.get("value")
            if not isinstance(name, str) or not isinstance(value, str):
                raise CredentialError(
                    "Credential payload requires name and value fields",
                    credential_id=credential_id,
                )
            return {"name": name, "value": value}

        raise CredentialError(
            f"Parsing not implemented for credential type '{credential_type.value}'",
            credential_id=credential_id,
        )

    def _load_key_material(self) -> tuple[str, str]:
        env_path = get_shared_env_path()
        if not os.path.exists(env_path):
            raise CredentialError("Shared credential environment file not found")

        env_values = self._load_env_file(env_path)
        key = env_values.get("SIG_KEY")
        salt = env_values.get("SIG_SALT")

        if not key or not salt:
            raise CredentialError("Missing SIG_KEY or SIG_SALT for credential decryption")

        return key, salt

    def _load_env_file(self, env_path: str) -> dict[str, str]:
        if dotenv_values is None:
            logger.warning(
                "python-dotenv not installed; cannot load shared .env file: %s", env_path
            )
            return {}

        try:
            values = dotenv_values(env_path) or {}
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Failed to load shared .env file %s: %s", env_path, str(exc))
            return {}

        return {key: value for key, value in values.items() if isinstance(value, str)}

    def _derive_key(self, key: str, salt: str) -> bytes:
        try:
            return hashlib.scrypt(
                key.encode("utf-8"),
                salt=salt.encode("utf-8"),
                n=16384,
                r=8,
                p=1,
                dklen=32,
            )
        except ValueError as exc:
            raise CredentialError("Unable to derive encryption key material") from exc
