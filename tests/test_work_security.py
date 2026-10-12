import asyncio
import json
import sqlite3

import pytest

from organizer import config, store
from organizer.security import LocalBrowserBoundary


@pytest.mark.parametrize(
    "kind,headers,expected",
    [
        ("http", {"host": "127.0.0.1:8775"}, 200),
        ("http", {"host": "evil.example:8775"}, 403),
        ("http", {"host": "127.0.0.1:8775", "origin": "https://evil.example"}, 403),
        ("http", {"host": "127.0.0.1:8775", "sec-fetch-site": "cross-site"}, 403),
        ("websocket", {"host": "127.0.0.1:8775", "origin": "https://evil.example"}, 1008),
    ],
)
def test_browser_boundary(kind, headers, expected):
    sent = []

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def send(message):
        sent.append(message)

    asyncio.run(
        LocalBrowserBoundary(app, 8775)(
            {"type": kind, "headers": [(k.encode(), v.encode()) for k, v in headers.items()]}, None, send
        )
    )
    assert sent[0].get("status", sent[0].get("code")) == expected
    if expected == 200:
        assert b"frame-ancestors 'none'" in dict(sent[0]["headers"])[b"content-security-policy"]


def test_personal_database_is_rejected_without_changes(tmp_path):
    path = tmp_path / "personal.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE items (id TEXT)")
        db.execute("PRAGMA user_version=7")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="Not a Sprig Work database"):
        store.initialize(path)
    assert path.read_bytes() == before


def test_personal_snapshot_is_rejected(workspace):
    path, _ = workspace
    payload = json.loads(store.export_snapshot(path))
    payload["format"] = "organize-snapshot"
    with pytest.raises(ValueError):
        store.parse_snapshot(json.dumps(payload))


def test_macos_path(monkeypatch):
    monkeypatch.setattr(config.sys, "platform", "darwin")
    assert str(config.database_path()).endswith(
        str(config.Path("Library/Application Support/SprigWork/workspace.db"))
    )
