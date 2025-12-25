"""Tests for Credential Manager."""

import base64
import hashlib
import json
from unittest.mock import AsyncMock, patch
from urllib.parse import quote

import pytest
import pytest_asyncio

from realtimex_toolkit import CredentialBundle, CredentialManager, CredentialType
from realtimex_toolkit.exceptions import ApiError, CredentialError


class TestCredentialManager:
    """Test CredentialManager class."""

    @pytest.fixture
    def mock_env_file_with_sig(self, tmp_path):
        """Create a temporary .env file with signature keys for testing."""
        env_content = (
            "SIG_KEY=test-signature-key\nSIG_SALT=test-signature-salt\nOPEN_AI_KEY=test-key\n"
        )
        env_file = tmp_path / ".env.development"
        env_file.write_text(env_content)
        return env_file

    @pytest.fixture
    def encrypted_credential(self):
        """Create an encrypted credential for testing."""
        # Use the same keys as in mock_env_file_with_sig
        key = "test-signature-key"
        salt = "test-signature-salt"

        # Derive encryption key
        encryption_key = hashlib.scrypt(
            key.encode("utf-8"),
            salt=salt.encode("utf-8"),
            n=16384,
            r=8,
            p=1,
            dklen=32,
        )

        # Create credential payload
        payload = {"name": "API_KEY", "value": "secret-value-123"}
        payload_json = json.dumps(payload)

        # Encrypt using AES-CBC (simplified for test)
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        iv = b"0123456789abcdef"  # 16 bytes IV
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(payload_json.encode("utf-8")) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # Format as expected by _decrypt_blob
        cipher_hex = ciphertext.hex()
        iv_hex = iv.hex()
        encrypted_text = f"{cipher_hex}:{iv_hex}"
        encoded_blob = base64.b64encode(encrypted_text.encode("utf-8")).decode("utf-8")

        return encoded_blob, payload

    @pytest_asyncio.fixture
    async def manager(self, mock_env_file_with_sig):
        """Create a CredentialManager instance for testing."""
        with patch("realtimex_toolkit.credentials.manager.get_shared_env_path") as mock_path:
            mock_path.return_value = str(mock_env_file_with_sig)
            manager = CredentialManager(
                base_url="https://api.example.com",
                api_key="test-key",
            )
            yield manager
            manager.close()

    @pytest.mark.asyncio
    async def test_get_credential_success(self, manager, encrypted_credential):
        """Test successful credential retrieval and decryption."""
        encoded_blob, expected_payload = encrypted_credential

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-123",
                "name": "Test Credential",
                "type": "env_var",
                "data": encoded_blob,
                "metadata": {"tags": ["production"]},
                "updated_at": "2025-01-01T00:00:00Z",
            },
        }

        manager._api_client.request = AsyncMock(return_value=api_response)

        result = manager.get("cred-123")

        assert isinstance(result, CredentialBundle)
        assert result.credential_id == "cred-123"
        assert result.name == "Test Credential"
        assert result.credential_type == CredentialType.ENV_VAR
        assert result.payload == expected_payload
        assert result.metadata == {"tags": ["production"]}
        assert result.updated_at == "2025-01-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_get_credential_caching(self, manager, encrypted_credential):
        """Test that credentials are cached after first retrieval."""
        encoded_blob, _ = encrypted_credential

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-cached",
                "name": "Cached Credential",
                "type": "http_header",
                "data": encoded_blob,
            },
        }

        manager._api_client.request = AsyncMock(return_value=api_response)

        # First call - should fetch from API
        result1 = manager.get("cred-cached")
        assert manager._api_client.request.call_count == 1

        # Second call - should use cache
        result2 = manager.get("cred-cached")
        assert manager._api_client.request.call_count == 1  # No additional call
        assert result1 is result2

    @pytest.mark.asyncio
    async def test_get_credential_encodes_identifier(self, manager, encrypted_credential):
        """Ensure credential identifiers are safely encoded before request."""
        encoded_blob, _ = encrypted_credential
        special_id = "name with spaces/#hash"

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-special",
                "name": "Special Credential",
                "type": "env_var",
                "data": encoded_blob,
            },
        }

        manager._api_client.request = AsyncMock(return_value=api_response)

        manager.get(special_id)

        method, path = manager._api_client.request.await_args.args
        assert method == "GET"
        assert path == f"/api/v1/credentials/{quote(special_id, safe='')}"

    @pytest.mark.asyncio
    async def test_get_credential_force_refresh(self, manager, encrypted_credential):
        """Test force_refresh bypasses cache."""
        encoded_blob, _ = encrypted_credential

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-refresh",
                "name": "Refresh Credential",
                "type": "basic_auth",
                "data": encoded_blob,
            },
        }

        # Create different encrypted payloads for username/password
        payload = {"username": "testuser", "password": "testpass"}
        payload_json = json.dumps(payload)

        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        encryption_key = manager._encryption_key
        iv = b"0123456789abcdef"
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(payload_json.encode("utf-8")) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        encrypted_text = f"{ciphertext.hex()}:{iv.hex()}"
        api_response["credential"]["data"] = base64.b64encode(
            encrypted_text.encode("utf-8")
        ).decode("utf-8")

        manager._api_client.request = AsyncMock(return_value=api_response)

        # First call
        manager.get("cred-refresh")
        assert manager._api_client.request.call_count == 1

        # Force refresh - should fetch again
        manager.get("cred-refresh", force_refresh=True)
        assert manager._api_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_get_credential_api_error(self, manager):
        """Test handling of API errors during credential fetch."""
        manager._api_client.request = AsyncMock(
            side_effect=ApiError("Network error", status_code=500)
        )

        with pytest.raises(CredentialError, match="Failed to fetch credential"):
            manager.get("cred-error")

    @pytest.mark.asyncio
    async def test_get_credential_status_false(self, manager):
        """Test handling of failure status in API response."""
        api_response = {"status": False}

        manager._api_client.request = AsyncMock(return_value=api_response)

        with pytest.raises(CredentialError, match="Credential service reported failure"):
            manager.get("cred-fail")

    @pytest.mark.asyncio
    async def test_get_after_close_raises(self, manager):
        """Ensure manager refuses operations once closed."""
        manager.close()
        manager.close()  # verify idempotent

        with pytest.raises(CredentialError, match="manager is closed"):
            manager.get("cred-closed")

    @pytest.mark.asyncio
    async def test_get_credential_malformed_response(self, manager):
        """Test handling of malformed API response."""
        api_response = {"status": True, "credential": "not-a-dict"}

        manager._api_client.request = AsyncMock(return_value=api_response)

        with pytest.raises(CredentialError, match="malformed credential payload"):
            manager.get("cred-malformed")

    @pytest.mark.asyncio
    async def test_unsupported_credential_type(self, manager, encrypted_credential):
        """Test handling of unsupported credential types."""
        encoded_blob, _ = encrypted_credential

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-unsupported",
                "type": "unsupported_type",
                "data": encoded_blob,
            },
        }

        manager._api_client.request = AsyncMock(return_value=api_response)

        with pytest.raises(CredentialError, match="Unsupported credential type"):
            manager.get("cred-unsupported")

    @pytest.mark.asyncio
    async def test_invalid_encrypted_data(self, manager):
        """Test handling of invalid base64 encrypted data."""
        api_response = {
            "status": True,
            "credential": {
                "id": "cred-invalid",
                "type": "env_var",
                "data": "not-valid-base64!!!",
            },
        }

        manager._api_client.request = AsyncMock(return_value=api_response)

        with pytest.raises(CredentialError, match="not valid base64"):
            manager.get("cred-invalid")

    @pytest.mark.asyncio
    async def test_clear_cache(self, manager):
        """Test cache clearing."""
        # Manually populate cache
        bundle = CredentialBundle(
            credential_id="test",
            name="Test",
            credential_type=CredentialType.ENV_VAR,
            payload={"key": "value"},
        )
        manager._cache["test"] = bundle

        assert "test" in manager._cache

        manager.clear_cache()

        assert len(manager._cache) == 0

    def test_credential_manager_init_missing_sig_keys(self, tmp_path):
        """Test CredentialManager initialization fails without signature keys."""
        env_file = tmp_path / ".env.development"
        env_file.write_text("SOME_KEY=value\n")

        with patch("realtimex_toolkit.credentials.manager.get_shared_env_path") as mock_path:
            mock_path.return_value = str(env_file)

            with pytest.raises(CredentialError, match="Missing SIG_KEY or SIG_SALT"):
                CredentialManager(base_url="https://api.example.com", api_key="test-key")

    def test_credential_manager_init_no_env_file(self):
        """Test CredentialManager initialization fails when env file doesn't exist."""
        with patch("realtimex_toolkit.credentials.manager.get_shared_env_path") as mock_path:
            mock_path.return_value = "/nonexistent/path/.env.development"

            with pytest.raises(CredentialError, match="environment file not found"):
                CredentialManager(base_url="https://api.example.com", api_key="test-key")


class TestGetCredentialConvenience:
    """Test get_credential convenience function."""

    @pytest.fixture
    def mock_env_file_with_sig(self, tmp_path):
        """Create a temporary .env file with signature keys for testing."""
        env_content = (
            "SIG_KEY=test-signature-key\nSIG_SALT=test-signature-salt\nOPEN_AI_KEY=test-key\n"
        )
        env_file = tmp_path / ".env.development"
        env_file.write_text(env_content)
        return env_file

    @pytest.fixture
    def encrypted_credential(self):
        """Create an encrypted credential for testing."""
        key = "test-signature-key"
        salt = "test-signature-salt"

        encryption_key = hashlib.scrypt(
            key.encode("utf-8"),
            salt=salt.encode("utf-8"),
            n=16384,
            r=8,
            p=1,
            dklen=32,
        )

        payload = {"name": "API_KEY", "value": "secret-value-123"}
        payload_json = json.dumps(payload)

        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        iv = b"0123456789abcdef"
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(payload_json.encode("utf-8")) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        cipher_hex = ciphertext.hex()
        iv_hex = iv.hex()
        encrypted_text = f"{cipher_hex}:{iv_hex}"
        encoded_blob = base64.b64encode(encrypted_text.encode("utf-8")).decode("utf-8")

        return encoded_blob, payload

    @pytest.mark.asyncio
    async def test_get_credential_success(self, mock_env_file_with_sig, encrypted_credential):
        """Test successful credential retrieval using convenience function."""
        from realtimex_toolkit.credentials import get_credential

        encoded_blob, expected_payload = encrypted_credential

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-456",
                "name": "Test Credential",
                "type": "env_var",
                "data": encoded_blob,
            },
        }

        with patch("realtimex_toolkit.credentials.manager.get_shared_env_path") as mock_path:
            mock_path.return_value = str(mock_env_file_with_sig)

            with patch(
                "realtimex_toolkit.api.http_client.ApiClient.request", new_callable=AsyncMock
            ) as mock_request:
                mock_request.return_value = api_response

                result = get_credential("cred-456", api_key="test-key")

                assert isinstance(result, dict)
                assert result["credential_id"] == "cred-456"
                assert result["name"] == "Test Credential"
                assert result["payload"] == expected_payload

    @pytest.mark.asyncio
    async def test_get_credential_with_custom_base_url(
        self, mock_env_file_with_sig, encrypted_credential
    ):
        """Test convenience function with custom base URL."""
        from realtimex_toolkit.credentials import get_credential

        encoded_blob, _ = encrypted_credential

        api_response = {
            "status": True,
            "credential": {
                "id": "cred-789",
                "type": "http_header",
                "data": encoded_blob,
            },
        }

        with patch("realtimex_toolkit.credentials.manager.get_shared_env_path") as mock_path:
            mock_path.return_value = str(mock_env_file_with_sig)

            with patch(
                "realtimex_toolkit.api.http_client.ApiClient.request", new_callable=AsyncMock
            ) as mock_request:
                mock_request.return_value = api_response

                result = get_credential(
                    "cred-456", api_key="test-key", base_url="https://custom-api.example.com"
                )

                assert isinstance(result, dict)
                assert result["credential_id"] == "cred-789"


class TestCredentialBundle:
    """Test CredentialBundle model."""

    def test_as_dict(self):
        """Test as_dict returns a copy of the payload."""
        bundle = CredentialBundle(
            credential_id="test-id",
            name="Test",
            credential_type=CredentialType.HTTP_HEADER,
            payload={"header": "Bearer token"},
        )

        result = bundle.as_dict()

        assert result == {"header": "Bearer token"}
        assert result is not bundle.payload  # Ensure it's a copy

    def test_masked_payload(self):
        """Test masked_payload masks all values."""
        bundle = CredentialBundle(
            credential_id="test-id",
            name="Test",
            credential_type=CredentialType.BASIC_AUTH,
            payload={"username": "user", "password": "secret"},
        )

        result = bundle.masked_payload()

        assert result == {"username": "[MASKED]", "password": "[MASKED]"}

    def test_credential_type_enum(self):
        """Test CredentialType enum values."""
        assert CredentialType.HTTP_HEADER == "http_header"
        assert CredentialType.QUERY_AUTH == "query_auth"
        assert CredentialType.BASIC_AUTH == "basic_auth"
        assert CredentialType.ENV_VAR == "env_var"
