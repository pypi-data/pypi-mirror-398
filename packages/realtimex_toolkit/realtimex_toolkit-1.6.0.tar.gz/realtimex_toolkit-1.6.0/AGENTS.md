# Repository Guidelines

## Project Structure & Module Organization
- `src/realtimex_toolkit/`: core package modules (agent flow, agent skills, credentials, LLM provider config, MCP helpers, utils).
- `tests/`: pytest suite covering public behaviors.
- `README.md`: user-facing usage; `USAGE.md`: flow variable guide; `dist/`: built artifacts.

## Build, Test, and Development Commands
- Install dev deps: `uv pip install -e ".[dev]"` (or `pip install -e ".[dev]"`).
- Run tests: `pytest` (add `-q` for quiet).
- Type checks: `mypy src/realtimex_toolkit`.
- Lint/format: `ruff check src/realtimex_toolkit tests` and `ruff format src/realtimex_toolkit tests`.

## Coding Style & Naming Conventions
- Python 3; 4-space indentation; prefer type hints everywhere.
- Keep functions small and side-effect aware; avoid over-abstraction.
- Naming: snake_case for functions/vars, PascalCase for classes; descriptive but concise.
- Use `pathlib` for paths; avoid hardcoded separators.
- Let `ruff` and `mypy` guide style; keep comments minimal and purposeful.

## Testing Guidelines
- Framework: `pytest`.
- Name tests with `test_*` and mirror module intent (`tests/test_mcp_gmail.py`, etc.).
- Isolate network by stubbing/mocking; do not depend on live services.
- Add regression tests for new public APIs and error paths.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject (e.g., “Add Gmail MCP lookup helper”), grouped by logical change.
- PRs: include summary, rationale, and testing notes; link issue/task if applicable. Provide screenshots only when UI changes apply (rare here).
- Ensure lint, type checks, and tests pass before requesting review.

## Security & Configuration Tips
- Do not commit secrets or local `.env` files. Tools load shared config from `~/.realtimex.ai/Resources/server/.env.development` when needed—never log or expose its contents.
- Prefer environment variables for credentials (e.g., `MCP_PROXY_API_KEY`, `MCP_PROXY_LINKED_ACCOUNT_OWNER_ID`).

## Agent-Specific Notes
- Workspace agent memory/skills live under `~/.realtimex.ai/Resources/agent-skills/workspaces/{workspace_slug}/{agent_id}/`; use `save_agent_memory` and `save_agent_skill`.
- Agent flow helpers (`get_flow_variable`, `get_workspace_slug`, `get_agent_id`, `get_workspace_data_dir`) should remain safe defaults-first and non-raising.***
