"""LLM provider configuration and credential management."""

import logging
import os
from collections.abc import Callable, Mapping
from pathlib import Path

from realtimex_toolkit.exceptions import CredentialError
from realtimex_toolkit.llm.mappings import PROVIDER_CREDENTIAL_MAPPINGS
from realtimex_toolkit.utils.path_utils import get_shared_env_path

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover
    dotenv_values = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class LLMProviderManager:
    """Manages LLM provider configurations and credential mapping for LiteLLM."""

    def __init__(
        self,
        providers: Mapping[str, Mapping[str, str]] | None = None,
        *,
        shared_env_path: Path | str | None = None,
    ) -> None:
        """Initialize the provider manager with explicit dependencies.

        Args:
            providers: Provider configurations mapping provider names to credential dicts.
                      Example: {"openai": {"OPEN_AI_KEY": "sk-..."}, "anthropic": {...}}
                      If None, all credentials will be loaded from shared env file.
            shared_env_path: Optional path to shared .env file for credential fallback.
                            If None, uses get_shared_env_path() from the RealtimeX ecosystem.
        """
        self.providers = providers or {}
        if shared_env_path is None:
            self.shared_env_path = Path(get_shared_env_path())
        else:
            self.shared_env_path = Path(shared_env_path)

    @classmethod
    def configure(
        cls,
        provider: str,
        *,
        providers: Mapping[str, Mapping[str, str]] | None = None,
        shared_env_path: Path | str | None = None,
        env_setter: Callable[[str, str], None] | None = None,
    ) -> dict[str, str]:
        """Configure provider using classmethod for utility-style invocation.

        This is the recommended way to configure a provider when working within
        the RealtimeX ecosystem. It uses the shared env file by default.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            providers: Optional provider credentials. If None, loads from shared env file.
            shared_env_path: Optional path to shared env file. If None, uses ecosystem default.
            env_setter: Optional callable to set env vars (for testing)

        Returns:
            Dictionary of environment variables that were set

        Raises:
            ValueError: If provider is not supported
            CredentialError: If required credentials are missing

        Example:
            >>> # Simple usage within RealtimeX ecosystem
            >>> LLMProviderManager.configure("openai")
            {'OPENAI_API_KEY': 'sk-...'}

            >>> # Explicit providers for testing
            >>> LLMProviderManager.configure(
            ...     "openai",
            ...     providers={"openai": {"OPEN_AI_KEY": "test-key"}}
            ... )
        """
        manager = cls(providers=providers, shared_env_path=shared_env_path)
        return manager.configure_provider(provider, env_setter=env_setter)

    def get_provider_env_vars(self, provider: str) -> dict[str, str]:
        """Get environment variables for a provider without setting them.

        This is a pure method that does not modify os.environ or any global state.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')

        Returns:
            Dictionary of LiteLLM-compatible environment variable mappings.
            Example: {"OPENAI_API_KEY": "sk-..."}

        Raises:
            ValueError: If provider is not supported (unknown provider name)
            CredentialError: If required credentials are missing for the provider
        """
        credentials = self._resolve_credentials(provider)
        return self._map_to_litellm_env_vars(provider, credentials)

    def apply_provider_env_vars(
        self,
        env_vars: dict[str, str],
        *,
        env_setter: Callable[[str, str], None] | None = None,
    ) -> None:
        """Apply environment variables to the process environment.

        This is a command method that mutates os.environ (or injected env_setter).

        Args:
            env_vars: Environment variables to set (from get_provider_env_vars)
            env_setter: Optional callable to set env vars. Defaults to os.environ.__setitem__.
                       Signature: (key: str, value: str) -> None
        """
        setter = env_setter or os.environ.__setitem__
        for key, value in env_vars.items():
            if value:
                setter(key, value)
                logger.debug(f"Set environment variable '{key}'")

    def configure_provider(
        self,
        provider: str,
        *,
        env_setter: Callable[[str, str], None] | None = None,
    ) -> dict[str, str]:
        """Get and apply environment variables for a provider.

        Convenience method that combines get_provider_env_vars() and apply_provider_env_vars().

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            env_setter: Optional callable to set env vars (for testing)

        Returns:
            Dictionary of environment variables that were set

        Raises:
            ValueError: If provider is not supported
            CredentialError: If required credentials are missing
        """
        env_vars = self.get_provider_env_vars(provider)
        self.apply_provider_env_vars(env_vars, env_setter=env_setter)
        logger.debug(f"Configured LiteLLM for provider: {provider}")
        return env_vars

    def _resolve_credentials(self, provider: str) -> dict[str, str]:
        """Resolve credentials for a provider (config -> shared env file fallback).

        Args:
            provider: Provider name

        Returns:
            Merged credentials dictionary
        """
        if provider in self.providers:
            credentials = dict(self.providers[provider])
            logger.debug(f"Using credentials for provider '{provider}' from config.")
            return credentials

        logger.debug(f"Provider '{provider}' not in config, checking shared env file.")
        return self._load_from_shared_env_file()

    def _load_from_shared_env_file(self) -> dict[str, str]:
        """Load credentials from shared env file if configured.

        Returns:
            Credentials dict from env file, or empty dict if unavailable
        """
        if not self.shared_env_path:
            logger.debug("No shared env path configured")
            return {}

        if not self.shared_env_path.exists():
            logger.debug(f"Shared environment file not found: {self.shared_env_path}")
            return {}

        if dotenv_values is None:
            logger.debug("python-dotenv not installed; skipping shared env file")
            return {}

        logger.debug(f"Loading credentials from shared file: {self.shared_env_path}")
        return dotenv_values(str(self.shared_env_path)) or {}

    def _map_to_litellm_env_vars(
        self,
        provider: str,
        credentials: dict[str, str],
    ) -> dict[str, str]:
        """Map provider credentials to LiteLLM environment variables.

        Args:
            provider: Provider name
            credentials: Source credentials dictionary

        Returns:
            Mapped environment variables for LiteLLM

        Raises:
            ValueError: If provider is not supported
            CredentialError: If required credential is missing
        """
        if provider not in PROVIDER_CREDENTIAL_MAPPINGS:
            raise ValueError(f"Unsupported provider: '{provider}'")

        env_vars: dict[str, str] = {}
        mappings = PROVIDER_CREDENTIAL_MAPPINGS[provider]

        for source_key, target_env_var, required in mappings:
            value = credentials.get(source_key, "")

            if required and not value:
                raise CredentialError(
                    f"Missing required credential '{source_key}' for provider '{provider}'"
                )

            if value:
                env_vars[target_env_var] = value

        return env_vars
