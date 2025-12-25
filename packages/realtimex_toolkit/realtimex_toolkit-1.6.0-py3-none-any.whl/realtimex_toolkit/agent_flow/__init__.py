"""Agent flow management utilities."""

import json
import os
import sys
from pathlib import Path
from typing import Any

from realtimex_toolkit.utils.path_utils import get_storage_db_path


def _resolve_dotted_path(data: dict[str, Any], path: str) -> tuple[bool, Any]:
    """Resolve a dotted path in nested dictionary.

    Args:
        data: Dictionary to search
        path: Dotted path like 'user.email' or simple key like 'name'

    Returns:
        Tuple of (found: bool, value: Any)
    """
    if not isinstance(data, dict):
        return False, None

    # Handle simple key (no dots)
    if "." not in path:
        if path in data:
            return True, data[path]
        return False, None

    # Traverse nested path
    keys = path.split(".")
    current = data

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]

    return True, current


def get_flow_variable(variable_name: str | None = None, default_value: Any = None) -> Any:
    """Retrieve flow variable from execution context.

    Supports both simple keys and dotted paths for nested variables.

    Args:
        variable_name: Variable name or dotted path (e.g., 'user.email').
                      If None, returns all variables.
        default_value: Value to return if variable not found (default: None)

    Returns:
        Variable value if found, otherwise default_value

    Examples:
        >>> get_flow_variable('user.email')
        'user@example.com'

        >>> get_flow_variable('user.name', 'Anonymous')
        'John Doe'

        >>> get_flow_variable()  # Returns all variables
        {'user': {'email': '...', 'name': '...'}, ...}
    """
    try:
        # Extract payload file path from command-line arguments
        if len(sys.argv) < 3:
            return default_value

        payload_file_path = sys.argv[2]

        if not os.path.exists(payload_file_path):
            return default_value

        with open(payload_file_path) as f:
            payload = json.load(f)

        if not payload:
            return default_value

        # Return all variables if no specific variable requested
        if variable_name is None:
            return payload

        # Try dotted path resolution first (handles nested variables)
        found, value = _resolve_dotted_path(payload, variable_name)
        if found:
            return value

        # Fall back to flat key lookup for backwards compatibility
        if variable_name in payload:
            return payload[variable_name]

        return default_value

    except Exception:
        return default_value


def get_workspace_slug(default_value: Any = None) -> Any:
    """Retrieve current workspace slug"""
    try:
        return get_flow_variable("workspace_slug", default_value=default_value)
    except Exception:
        return default_value


def get_thread_id(default_value: Any = None) -> Any:
    """Retrieve current thread id"""
    try:
        return get_flow_variable("thread_id", default_value=default_value)
    except Exception:
        return default_value


def get_agent_id(default_value: Any = None) -> Any:
    """Retrieve current agent id"""
    try:
        return get_flow_variable("agent_id", default_value=default_value)
    except Exception:
        return default_value


def get_workspace_data_dir(
    variable_name: str | None = None, default_workspace_slug: Any = None
) -> Any:
    """Retrieve flow variable"""
    try:
        import os

        workspace_slug = get_workspace_slug(default_value=default_workspace_slug)
        realtimex_dir = os.path.join(os.path.expanduser("~"), ".realtimex.ai")
        realtimex_storage_dir = os.path.realpath(
            os.path.join(realtimex_dir, "Resources", "server", "storage")
        )

        if not os.path.exists(realtimex_storage_dir):
            return None

        workspace_data_dir = os.path.join(realtimex_storage_dir, "working-data", workspace_slug)

        if not os.path.exists(workspace_data_dir):
            os.makedirs(workspace_data_dir, exist_ok=True)

        return workspace_data_dir

    except Exception:
        return None


def schedule_agent_flow_run(
    flow_uuid: str,
    interval_config: dict[str, Any],
    *,
    flow_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    mode: str = "schedule",
) -> int:
    """Schedule a future agent flow execution by inserting into SQLite.

    Args:
        flow_uuid: Required flow identifier.
        interval_config: Required scheduling config (stored as JSON).
        flow_name: Optional flow name.
        metadata: Optional metadata dict (stored as JSON).
        mode: Scheduling mode, defaults to "schedule".

    Returns:
        SQLite rowid of the inserted schedule record.

    Raises:
        ValueError: If required arguments are missing.
        sqlite3.Error: On database operation errors.
    """
    import sqlite3  # Lazy import to avoid overhead when unused

    if not flow_uuid:
        raise ValueError("flow_uuid is required")
    if not interval_config:
        raise ValueError("interval_config is required")

    db_path = Path(get_storage_db_path())
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    interval_json = json.dumps(interval_config)
    metadata_json = json.dumps(metadata or {})

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO agent_flow_schedule_runs
                (flowUuid, flowName, mode, intervalConfig, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                flow_uuid,
                flow_name or "",
                mode,
                interval_json,
                metadata_json,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def update_agent_flow_run(
    schedule_id: int,
    *,
    flow_uuid: str | None = None,
    interval_config: dict[str, Any] | None = None,
    flow_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    mode: str | None = None,
    active: bool | None = None,
) -> int:
    """Update an existing scheduled agent flow record by rowid.

    Args:
        schedule_id: Rowid of the schedule record to update.
        flow_uuid: Optional new flow UUID.
        interval_config: Optional new interval config (stored as JSON).
        flow_name: Optional new flow name.
        metadata: Optional metadata dict (stored as JSON).
        mode: Optional new mode value.
        active: Optional active flag (boolean).

    Returns:
        Number of rows updated (0 if not found).

    Raises:
        ValueError: If schedule_id is invalid or no fields provided.
        sqlite3.Error: On database operation errors.
    """
    import sqlite3  # Lazy import

    if schedule_id is None or schedule_id <= 0:
        raise ValueError("schedule_id must be a positive integer")

    updates: list[str] = []
    params: list[Any] = []

    if flow_uuid is not None:
        updates.append("flowUuid = ?")
        params.append(flow_uuid)
    if interval_config is not None:
        updates.append("intervalConfig = ?")
        params.append(json.dumps(interval_config))
    if flow_name is not None:
        updates.append("flowName = ?")
        params.append(flow_name)
    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))
    if mode is not None:
        updates.append("mode = ?")
        params.append(mode)
    if active is not None:
        updates.append("active = ?")
        params.append(1 if active else 0)

    if not updates:
        raise ValueError("At least one field must be provided to update")

    db_path = Path(get_storage_db_path())
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    params.append(schedule_id)

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            f"UPDATE agent_flow_schedule_runs SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


__all__ = [
    "get_agent_id",
    "get_flow_variable",
    "get_thread_id",
    "get_workspace_data_dir",
    "get_workspace_slug",
    "schedule_agent_flow_run",
    "update_agent_flow_run",
]
