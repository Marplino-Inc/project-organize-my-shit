import json
import sqlite3

import pytest

from organizer import store
from tests.test_store import child


def test_symbol_migration_and_legacy_import(workspace):
    path, root = workspace
    child(path, root)
    with sqlite3.connect(path) as db:
        db.execute("ALTER TABLE items DROP COLUMN symbol")
        db.execute("PRAGMA user_version=6")
    store.initialize(path)
    store.initialize(path)
    assert all(item["symbol"] == "circle" for item in store.load(path)[0])
    backups = list(path.parent.glob("test.pre-v1.2.0-*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 6
        assert "symbol" not in {x[1] for x in db.execute("PRAGMA table_info(items)")}
    payload = json.loads(store.export_snapshot(path))
    payload["version"] = 4
    for item in payload["items"]:
        del item["symbol"]
    assert all(item.symbol == "circle" for item in store.parse_snapshot(json.dumps(payload)).items)


@pytest.mark.parametrize("symbol", store.PROJECT_SYMBOLS)
def test_symbol_round_trip_and_validation(workspace, symbol):
    path, root = workspace
    updated = store.save(path, {"symbol": symbol}, root["id"], root["revision"], actor="Agent")
    snapshot = store.parse_snapshot(store.export_snapshot(path))
    assert snapshot.version == 5
    assert snapshot.items[0].symbol == symbol
    assert updated["revision"] == root["revision"] + 1
    with pytest.raises(ValueError):
        store.save(path, {"symbol": "arbitrary_html"}, updated["id"], updated["revision"])
    task = child(path, updated)
    with pytest.raises(ValueError, match="Only projects"):
        store.save(path, {"symbol": "star"}, task["id"], task["revision"])
