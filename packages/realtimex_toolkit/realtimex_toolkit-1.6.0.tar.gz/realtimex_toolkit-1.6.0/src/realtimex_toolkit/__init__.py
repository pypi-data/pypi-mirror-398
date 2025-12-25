"""RealtimeX Internal Utilities - Lightweight library for LLM and credential management."""

__version__ = "1.1.0"

from realtimex_toolkit.agent_flow import (
    get_agent_id,
    get_flow_variable,
    get_thread_id,
    get_workspace_data_dir,
    get_workspace_slug,
    schedule_agent_flow_run,
    update_agent_flow_run,
)
from realtimex_toolkit.agent_skills import (
    save_agent_memory,
    save_agent_skill,
)
from realtimex_toolkit.credentials import (
    CredentialBundle,
    CredentialManager,
    CredentialType,
    get_credential,
)
from realtimex_toolkit.exceptions import (
    ApiError,
    AuthenticationError,
    ConnectionError,
    CredentialError,
    ProviderError,
    RateLimitError,
    RealtimeXError,
    ResourceNotFoundError,
    ServerError,
)
from realtimex_toolkit.llm import LLMProviderManager, configure_provider, get_provider_env_vars
from realtimex_toolkit.mcp import get_gmail_email

__all__ = [  # noqa: RUF022
    # Version
    "__version__",
    # Exceptions
    "ApiError",
    "AuthenticationError",
    "ConnectionError",
    "CredentialError",
    "ProviderError",
    "RateLimitError",
    "RealtimeXError",
    "ResourceNotFoundError",
    "ServerError",
    # LLM
    "LLMProviderManager",
    "configure_provider",
    "get_provider_env_vars",
    # Credentials
    "CredentialBundle",
    "CredentialManager",
    "CredentialType",
    "get_credential",
    # Agent
    "save_agent_memory",
    "save_agent_skill",
    # MCP
    "get_gmail_email",
    # Agent Flow
    "get_flow_variable",
    "get_thread_id",
    "get_workspace_slug",
    "get_workspace_data_dir",
    "get_agent_id",
    "schedule_agent_flow_run",
    "update_agent_flow_run",
]
