from pathlib import Path

import pytest

from realtimex_toolkit import agent_skills


@pytest.fixture()
def user_dir(tmp_path, monkeypatch):
    """Point toolkit user dir to temp location."""
    root = tmp_path / ".realtimex.ai"
    monkeypatch.setattr(
        "realtimex_toolkit.utils.path_utils.get_realtimex_user_dir",
        lambda: str(root),
    )
    # Reload module to pick up patched path resolver
    import importlib

    importlib.reload(agent_skills)
    return root


def test_append_agent_memory_creates_and_appends(user_dir):
    path = agent_skills.save_agent_memory("workspace", "agent1", "First line")

    agent_path = Path(path)
    assert agent_path.read_text(encoding="utf-8") == "First line"

    # Append adds newline separator when needed
    agent_skills.save_agent_memory("workspace", "agent1", "Second line", mode="append")
    assert agent_path.read_text(encoding="utf-8") == "First line\nSecond line"


def test_write_skill_document_overwrites(user_dir):
    path = agent_skills.save_agent_skill("ws1", "agent1", "web-research", "# Skill Doc")

    skill_path = Path(path)
    assert skill_path.name == "SKILL.md"
    assert skill_path.parent.name == "web-research"
    assert skill_path.read_text(encoding="utf-8") == "# Skill Doc"

    # Overwrite behavior
    agent_skills.save_agent_skill("ws1", "agent1", "web-research", "Updated")
    assert skill_path.read_text(encoding="utf-8") == "Updated"

    # Append behavior
    agent_skills.save_agent_skill("ws1", "agent1", "web-research", "More", mode="append")
    assert skill_path.read_text(encoding="utf-8") == "Updated\nMore"
