"""Workspace agent memory and skill documentation utilities."""

from pathlib import Path
from typing import Literal

from realtimex_toolkit.utils.path_utils import get_realtimex_user_dir


def _workspace_agent_root(workspace_slug: str, agent_id: str) -> Path:
    """Return the workspace agent root directory."""
    return (
        Path(get_realtimex_user_dir())
        / "Resources"
        / "agent-skills"
        / "workspaces"
        / workspace_slug
        / agent_id
    )


def save_agent_memory(
    workspace_slug: str,
    agent_id: str,
    content: str,
    *,
    mode: Literal["overwrite", "append"] = "overwrite",
) -> str:
    """Save content to the workspace agent.md file.

    Creates the directory and file if they do not exist. When append=True,
    content is appended with a newline separator if the file is non-empty.

    Args:
        workspace_slug: Workspace slug to target.
        agent_id: Agent identifier within the workspace.
        content: Markdown content to append.
        mode: "overwrite" (default) or "append".

    Returns:
        The absolute path to the agent.md file as a string.
    """
    agent_root = _workspace_agent_root(workspace_slug, agent_id)
    agent_path = agent_root / "agent.md"
    agent_root.mkdir(parents=True, exist_ok=True)

    if mode == "append":
        needs_newline = agent_path.exists() and agent_path.stat().st_size > 0
        with agent_path.open("a", encoding="utf-8") as f:
            if needs_newline and not content.startswith("\n"):
                f.write("\n")
            f.write(content)
    elif mode == "overwrite":
        agent_path.write_text(content, encoding="utf-8")
    else:
        raise ValueError("mode must be 'overwrite' or 'append'")

    return str(agent_path)


def save_agent_skill(
    workspace_slug: str,
    agent_id: str,
    skill_name: str,
    content: str,
    *,
    mode: Literal["overwrite", "append"] = "overwrite",
) -> str:
    """Write a skill markdown document into the workspace skills directory.

    Overwrites existing SKILL.md content for the given skill name by default.
    Creates parent directories as needed. When append=True, content is appended.

    Args:
        workspace_slug: Workspace slug to target.
        agent_id: Agent identifier within the workspace.
        skill_name: Skill folder name (e.g., "web-research").
        content: Markdown content to write to SKILL.md.
        mode: "overwrite" (default) or "append".

    Returns:
        The absolute path to the skill file as a string.
    """
    agent_root = _workspace_agent_root(workspace_slug, agent_id)
    skill_dir = agent_root / "skills" / skill_name
    skill_path = skill_dir / "SKILL.md"

    skill_dir.mkdir(parents=True, exist_ok=True)
    if mode == "append":
        if skill_path.exists() and skill_path.stat().st_size > 0:
            with skill_path.open("a", encoding="utf-8") as f:
                if not content.startswith("\n"):
                    f.write("\n")
                f.write(content)
        else:
            skill_path.write_text(content, encoding="utf-8")
    elif mode == "overwrite":
        skill_path.write_text(content, encoding="utf-8")
    else:
        raise ValueError("mode must be 'overwrite' or 'append'")

    return str(skill_path)


__all__ = [
    "save_agent_memory",
    "save_agent_skill",
]
