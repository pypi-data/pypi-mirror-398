"""Tests for LLM provider configuration."""

import os
from pathlib import Path

import pytest

from realtimex_toolkit import LLMProviderManager, configure_provider, get_provider_env_vars
from realtimex_toolkit.exceptions import CredentialError


class TestLLMProviderManager:
    """Test LLMProviderManager class."""

    def test_get_credentials_from_config(self):
        """Test that credentials from config are returned as env vars."""
        providers = {"openai": {"OPEN_AI_KEY": "test-config-key"}}
        manager = LLMProviderManager(providers=providers, shared_env_path="")

        env_vars = manager.get_provider_env_vars("openai")

        assert env_vars == {"OPENAI_API_KEY": "test-config-key"}

    def test_fallback_to_env_file(self, mock_env_file):
        """Provider not in config should fall back to shared .env file."""
        manager = LLMProviderManager(providers={}, shared_env_path=mock_env_file)
        env_vars = manager.get_provider_env_vars("openai")

        assert env_vars == {"OPENAI_API_KEY": "test-key-from-file"}

    def test_config_overrides_env_file(self, mock_env_file):
        """Configured credentials take precedence over shared .env file."""
        providers = {"openai": {"OPEN_AI_KEY": "test-config-key"}}
        manager = LLMProviderManager(providers=providers, shared_env_path=mock_env_file)

        env_vars = manager.get_provider_env_vars("openai")

        assert env_vars == {"OPENAI_API_KEY": "test-config-key"}

    def test_missing_credentials_raises_error(self):
        """Missing config and shared file should raise CredentialError."""
        manager = LLMProviderManager(providers={}, shared_env_path="")

        with pytest.raises(
            CredentialError,
            match="Missing required credential 'OPEN_AI_KEY' for provider 'openai'",
        ):
            manager.get_provider_env_vars("openai")

    def test_unsupported_provider_raises_error(self):
        """Unsupported provider should raise ValueError."""
        manager = LLMProviderManager(providers={}, shared_env_path="")

        with pytest.raises(ValueError, match="Unsupported provider: 'unknown-provider'"):
            manager.get_provider_env_vars("unknown-provider")

    def test_configure_provider_sets_env_vars(self):
        """Test that configure_provider correctly sets environment variables."""
        providers = {"openai": {"OPEN_AI_KEY": "test-env-key"}}
        manager = LLMProviderManager(providers=providers, shared_env_path="")

        result = manager.configure_provider("openai")

        assert os.environ.get("OPENAI_API_KEY") == "test-env-key"
        assert result == {"OPENAI_API_KEY": "test-env-key"}

        del os.environ["OPENAI_API_KEY"]

    def test_multi_credential_provider(self):
        """Test provider requiring multiple credentials (Azure)."""
        providers = {
            "azure": {
                "AZURE_OPENAI_KEY": "test-azure-key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            }
        }
        manager = LLMProviderManager(providers=providers, shared_env_path="")

        env_vars = manager.get_provider_env_vars("azure")

        assert env_vars == {
            "AZURE_OPENAI_API_KEY": "test-azure-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        }

    def test_optional_credentials(self):
        """Test providers with optional credentials (localai)."""
        providers = {"localai": {"LOCAL_AI_BASE_PATH": "http://localhost:8080"}}
        manager = LLMProviderManager(providers=providers, shared_env_path="")

        env_vars = manager.get_provider_env_vars("localai")

        assert env_vars == {"OPENAI_API_BASE": "http://localhost:8080"}


class TestClassmethodConfigure:
    """Test the classmethod configure() for utility-style usage."""

    def test_configure_with_explicit_providers(self):
        """Test configure() classmethod with explicit providers."""
        providers = {"openai": {"OPEN_AI_KEY": "test-classmethod-key"}}
        mock_setter = {}

        def setter(key, value):
            mock_setter[key] = value

        result = LLMProviderManager.configure(
            "openai",
            providers=providers,
            shared_env_path="",
            env_setter=setter,
        )

        assert result == {"OPENAI_API_KEY": "test-classmethod-key"}
        assert mock_setter == {"OPENAI_API_KEY": "test-classmethod-key"}

    def test_configure_with_shared_env_file(self, mock_env_file):
        """Test configure() classmethod falls back to shared env file."""
        mock_setter = {}

        def setter(key, value):
            mock_setter[key] = value

        result = LLMProviderManager.configure(
            "anthropic",
            providers={},
            shared_env_path=mock_env_file,
            env_setter=setter,
        )

        assert result == {"ANTHROPIC_API_KEY": "test-anthropic-key"}
        assert mock_setter == {"ANTHROPIC_API_KEY": "test-anthropic-key"}


class TestConvenienceFunctions:
    """Test top-level convenience functions."""

    def test_configure_provider_function(self):
        """Test configure_provider() convenience function."""
        providers = {"openai": {"OPEN_AI_KEY": "test-convenience-key"}}
        mock_setter = {}

        def setter(key, value):
            mock_setter[key] = value

        result = configure_provider(
            "openai",
            providers=providers,
            shared_env_path="",
            env_setter=setter,
        )

        assert result == {"OPENAI_API_KEY": "test-convenience-key"}
        assert mock_setter == {"OPENAI_API_KEY": "test-convenience-key"}

    def test_get_provider_env_vars_function(self):
        """Test get_provider_env_vars() convenience function."""
        providers = {"openai": {"OPEN_AI_KEY": "test-get-key"}}

        env_vars = get_provider_env_vars("openai", providers=providers, shared_env_path="")

        assert env_vars == {"OPENAI_API_KEY": "test-get-key"}


class TestPathHandling:
    """Test path handling for shared env file."""

    def test_path_object_as_shared_env_path(self, mock_env_file):
        """Test that Path objects are accepted for shared_env_path."""
        manager = LLMProviderManager(providers={}, shared_env_path=Path(mock_env_file))
        env_vars = manager.get_provider_env_vars("openai")

        assert env_vars == {"OPENAI_API_KEY": "test-key-from-file"}

    def test_string_path_as_shared_env_path(self, mock_env_file):
        """Test that string paths are accepted for shared_env_path."""
        manager = LLMProviderManager(providers={}, shared_env_path=str(mock_env_file))
        env_vars = manager.get_provider_env_vars("openai")

        assert env_vars == {"OPENAI_API_KEY": "test-key-from-file"}
