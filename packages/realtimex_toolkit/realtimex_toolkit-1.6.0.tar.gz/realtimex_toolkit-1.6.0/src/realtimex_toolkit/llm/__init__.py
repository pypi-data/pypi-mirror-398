"""LLM provider configuration utilities."""

from realtimex_toolkit.llm.providers import LLMProviderManager


def configure_provider(provider: str, **kwargs) -> dict[str, str]:
    """Configure LLM provider and set environment variables.

    Convenience function wrapping LLMProviderManager.configure().

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        **kwargs: Additional arguments passed to LLMProviderManager.configure()

    Returns:
        Dictionary of environment variables that were set

    Example:
        >>> configure_provider("openai")
        {'OPENAI_API_KEY': 'sk-...'}
    """
    return LLMProviderManager.configure(provider, **kwargs)


def get_provider_env_vars(provider: str, **kwargs) -> dict[str, str]:
    """Get provider environment variables without setting them.

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        **kwargs: Additional arguments passed to LLMProviderManager constructor

    Returns:
        Dictionary of LiteLLM-compatible environment variables

    Example:
        >>> get_provider_env_vars("anthropic")
        {'ANTHROPIC_API_KEY': 'sk-ant-...'}
    """
    manager = LLMProviderManager(**kwargs)
    return manager.get_provider_env_vars(provider)


__all__ = [
    "LLMProviderManager",
    "configure_provider",
    "get_provider_env_vars",
]
