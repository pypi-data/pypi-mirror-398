# /// script
# dependencies = ["realtimex_toolkit==1.6.0b2"]
# ///

"""Quick test script for schedule_agent_flow_run with a local dev install.

Run with:
    uv run scripts/test_schedule_flow.py
"""

import sqlite3
from pathlib import Path

from realtimex_toolkit import schedule_agent_flow_run, update_agent_flow_run
from realtimex_toolkit.utils.path_utils import get_realtimex_user_dir


def ensure_schema(db_path: Path) -> None:
    """Create the schedule table if it doesn't exist (for local testing)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_flow_schedule_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flowUuid TEXT NOT NULL,
                flowName TEXT,
                mode TEXT NOT NULL,
                intervalConfig TEXT NOT NULL,
                metadata TEXT
            )
            """
        )


def main() -> None:
    user_dir = Path(get_realtimex_user_dir())
    db_path = user_dir / "Resources" / "server" / "storage" / "realtimex.db"
    ensure_schema(db_path)

    rowid = schedule_agent_flow_run(
        flow_uuid="dev-flow-uuid",
        interval_config={"datetime": "2025-12-17T08:54:00.0000z"},
        flow_name="demo-flow",
        metadata={"note": "scheduled via test script"},
    )
    print(f"Inserted schedule with rowid={rowid}")

    updated = update_agent_flow_run(
        schedule_id=rowid,
        flow_name="demo-flow-updated",
        metadata={"note": "updated via test script"},
        active=True,
    )
    print(f"Updated rows: {updated}")

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT id, flowName, active FROM agent_flow_schedule_runs"
        )
        rows = cur.fetchall()

    print(f"Total scheduled rows: {len(rows)}")
    if rows:
        first = rows[0]
        print(f"First row -> id={first[0]}, flowName={first[1]}, active={first[2]}")


if __name__ == "__main__":
    main()
