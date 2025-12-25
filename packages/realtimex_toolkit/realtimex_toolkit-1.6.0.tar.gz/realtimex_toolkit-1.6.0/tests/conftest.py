"""Shared pytest fixtures for realtimex_toolkit tests."""

import pytest


@pytest.fixture
def mock_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_content = "OPEN_AI_KEY=test-key-from-file\nANTHROPIC_API_KEY=test-anthropic-key\n"
    env_file = tmp_path / ".env.development"
    env_file.write_text(env_content)
    return env_file
