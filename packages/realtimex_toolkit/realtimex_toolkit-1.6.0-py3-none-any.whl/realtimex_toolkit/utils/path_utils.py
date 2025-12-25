"""Path-related utility functions for RealtimeX ecosystem."""

import os

try:  # Optional dependency used across the toolkit
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover
    dotenv_values = None  # type: ignore[assignment]


def get_realtimex_user_dir() -> str:
    """Returns the path to the .realtimex.ai user directory.

    Returns:
        Path to the user directory (e.g., ~/.realtimex.ai)
    """
    return os.path.join(os.path.expanduser("~"), ".realtimex.ai")


def get_shared_env_path() -> str:
    """Returns the fixed path to the shared environment file.

    Returns:
        Path to the shared .env.development file
    """
    user_dir = get_realtimex_user_dir()
    return os.path.realpath(os.path.join(user_dir, "Resources", "server", ".env.development"))


def get_env_value(key: str, *, shared_env_path: str | None = None) -> str | None:
    """Get value from environment or shared .env.development file."""
    value = os.getenv(key)
    if value:
        return value

    env_path = shared_env_path or get_shared_env_path()
    if not env_path or not os.path.exists(env_path):
        return None

    if dotenv_values is None:  # pragma: no cover - handled via dependency
        return None

    values = dotenv_values(env_path) or {}
    return values.get(key)  # type: ignore[no-any-return]


def get_storage_db_path() -> str:
    """Return the path to the shared storage SQLite database."""
    return os.path.realpath(
        os.path.join(get_realtimex_user_dir(), "Resources", "server", "storage", "realtimex.db")
    )
