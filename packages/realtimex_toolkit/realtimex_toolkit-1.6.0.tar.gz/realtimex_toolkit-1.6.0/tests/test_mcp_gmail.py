import pytest

from realtimex_toolkit.mcp import gmail


def test_get_gmail_email_happy_path(monkeypatch):
    calls = []

    def fake_fetch(url, headers, params=None):
        calls.append((url, headers, params))
        if "linked-accounts?" in url or ("linked-accounts" in url and params):
            return [
                {"id": "acc-1", "app_name": "GMAIL", "enabled": True},
            ]
        if url.endswith("/linked-accounts/acc-1"):
            return {"security_credentials": {"access_token": "token-123"}}
        if "gmail.googleapis.com" in url:
            return {"emailAddress": "user@example.com"}
        raise AssertionError(f"Unexpected url {url}")

    monkeypatch.setattr(gmail, "sync_fetch_json", fake_fetch)

    email = gmail.get_gmail_email(
        linked_account_owner_id="owner-1",
        api_key="api-key",
        base_url="https://mcp.realtimex.ai",
    )

    assert email == "user@example.com"
    assert any("linked-accounts" in call[0] for call in calls)
    assert any("gmail.googleapis.com" in call[0] for call in calls)


def test_get_gmail_email_missing_account(monkeypatch):
    monkeypatch.setattr(gmail, "sync_fetch_json", lambda *a, **k: [])

    with pytest.raises(Exception, match="No GMAIL linked accounts"):
        gmail.get_gmail_email(
            linked_account_owner_id="owner-1",
            api_key="api-key",
        )


def test_get_gmail_email_requires_credentials(monkeypatch):
    monkeypatch.delenv("MCP_PROXY_API_KEY", raising=False)
    monkeypatch.delenv("MCP_PROXY_LINKED_ACCOUNT_OWNER_ID", raising=False)
    monkeypatch.setattr(
        "realtimex_toolkit.utils.path_utils.get_shared_env_path",
        lambda: "/nonexistent/.env.development",
    )

    with pytest.raises(ValueError, match="MCP_PROXY_LINKED_ACCOUNT_OWNER_ID"):
        gmail.get_gmail_email(api_key="api-key")

    with pytest.raises(ValueError, match="MCP_PROXY_API_KEY"):
        gmail.get_gmail_email(linked_account_owner_id="owner-1")


def test_get_gmail_email_reads_shared_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env.development"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(
        "MCP_PROXY_API_KEY=env-api\nMCP_PROXY_LINKED_ACCOUNT_OWNER_ID=env-owner\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("MCP_PROXY_API_KEY", raising=False)
    monkeypatch.delenv("MCP_PROXY_LINKED_ACCOUNT_OWNER_ID", raising=False)
    monkeypatch.setattr(
        "realtimex_toolkit.utils.path_utils.get_shared_env_path",
        lambda: str(env_file),
    )

    def fake_fetch(url, headers, params=None):
        if params is not None:
            return [{"id": "acc-1", "app_name": "GMAIL"}]
        if url.endswith("/acc-1"):
            return {"security_credentials": {"access_token": "token-123"}}
        if "gmail.googleapis.com" in url:
            return {"emailAddress": "user@example.com"}
        raise AssertionError(f"Unexpected url {url}")

    monkeypatch.setattr(gmail, "sync_fetch_json", fake_fetch)

    email = gmail.get_gmail_email()

    assert email == "user@example.com"
