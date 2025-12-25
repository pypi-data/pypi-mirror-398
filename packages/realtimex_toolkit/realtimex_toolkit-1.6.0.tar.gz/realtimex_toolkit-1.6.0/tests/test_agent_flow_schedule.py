import json
import sqlite3
from pathlib import Path

from realtimex_toolkit.agent_flow import schedule_agent_flow_run


def test_schedule_agent_flow_run_inserts_record(monkeypatch, tmp_path):
    # Point toolkit to temp user dir
    user_dir = tmp_path / ".realtimex.ai"
    monkeypatch.setattr(
        "realtimex_toolkit.agent_flow.get_realtimex_user_dir",
        lambda: str(user_dir),
    )

    # Precreate DB and table to mimic existing schema
    db_path = Path(user_dir) / "Resources" / "server" / "storage" / "realtimex.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE agent_flow_schedule_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flowUuid TEXT NOT NULL,
                flowName TEXT,
                mode TEXT NOT NULL,
                intervalConfig TEXT NOT NULL,
                metadata TEXT,
                active BOOLEAN
            )
            """
        )

    flow_uuid = "flow-123"
    interval = {"datetime": "2025-12-17T08:54:00.0000z"}
    metadata = {"k": "v"}
    flow_name = "My Flow"

    rowid = schedule_agent_flow_run(
        flow_uuid,
        interval,
        flow_name=flow_name,
        metadata=metadata,
    )

    assert rowid > 0

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT flowUuid, flowName, mode, intervalConfig, metadata, active FROM agent_flow_schedule_runs"
        )
        row = cur.fetchone()

    assert row[0] == flow_uuid
    assert row[1] == flow_name
    assert row[2] == "schedule"
    assert json.loads(row[3]) == interval
    assert json.loads(row[4]) == metadata
    assert row[5] is None  # active not set on insert


def test_update_agent_flow_run(monkeypatch, tmp_path):
    user_dir = tmp_path / ".realtimex.ai"
    monkeypatch.setattr(
        "realtimex_toolkit.agent_flow.get_realtimex_user_dir",
        lambda: str(user_dir),
    )

    db_path = Path(user_dir) / "Resources" / "server" / "storage" / "realtimex.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE agent_flow_schedule_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flowUuid TEXT NOT NULL,
                flowName TEXT,
                mode TEXT NOT NULL,
                intervalConfig TEXT NOT NULL,
                metadata TEXT,
                active BOOLEAN
            )
            """
        )
        conn.execute(
            """
            INSERT INTO agent_flow_schedule_runs
                (flowUuid, flowName, mode, intervalConfig, metadata, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "flow-123",
                "Old Name",
                "schedule",
                json.dumps({"datetime": "2025-12-17T08:54:00.0000z"}),
                json.dumps({"k": "v"}),
                1,
            ),
        )
        conn.commit()

    from realtimex_toolkit.agent_flow import update_agent_flow_run

    updated = update_agent_flow_run(
        1,
        flow_name="New Name",
        metadata={"k": "updated"},
        active=False,
    )

    assert updated == 1

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT flowName, metadata, active FROM agent_flow_schedule_runs WHERE id = 1"
        )
        row = cur.fetchone()

    assert row[0] == "New Name"
    assert json.loads(row[1]) == {"k": "updated"}
    assert row[2] == 0
