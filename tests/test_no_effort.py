import json
import sqlite3

import pytest

from organizer import store
from organizer.cli import main as cli
from organizer.reports import html_report
from tests.test_store import child


def test_upgrade_removes_effort_with_restorable_backup(workspace):
    path, root = workspace
    task = child(path, root, tags={"area": "UI"})
    with sqlite3.connect(path) as db:
        db.execute("ALTER TABLE items ADD COLUMN effort INTEGER")
        db.execute("UPDATE items SET effort=4 WHERE id=?", (task["id"],))
        db.execute("INSERT INTO settings VALUES ('effort_scale', 'T-shirt')")
        db.execute("PRAGMA user_version=4")
    store.initialize(path)
    store.initialize(path)
    assert next(x for x in store.load(path)[0] if x["id"] == task["id"]) == task
    assert store.setting(path, "effort_scale") is None
    assert "effort" not in store.export_snapshot(path)
    assert "Effort" not in html_report(store.load(path)[0])
    backups = list(path.parent.glob("test.pre-v0.3.0-*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute("SELECT effort FROM items WHERE id=?", (task["id"],)).fetchone()[0] == 4
    with sqlite3.connect(path) as db:
        assert "effort" not in [row[1] for row in db.execute("PRAGMA table_info(items)")]


def test_agents_cannot_read_or_write_effort(workspace, capsys):
    path, root = workspace
    with pytest.raises(ValueError, match="read-only fields"):
        child(path, root, effort=2)
    assert cli(["schema"]) == 0
    result = json.loads(capsys.readouterr().out)["data"]
    assert result["api_version"] == 3
    assert "effort" not in result["schema"]["properties"]
