import pytest

from organizer import store
from tests.test_store import child


@pytest.mark.parametrize("symbol", store.PROJECT_SYMBOLS)
def test_symbol_round_trip_and_validation(workspace, symbol):
    path, root = workspace
    updated = store.save(path, {"symbol": symbol}, root["id"], root["revision"], actor="Agent")
    snapshot = store.parse_snapshot(store.export_snapshot(path))
    assert snapshot.version == 1
    assert snapshot.items[0].symbol == symbol
    assert updated["revision"] == root["revision"] + 1
    with pytest.raises(ValueError):
        store.save(path, {"symbol": "arbitrary_html"}, updated["id"], updated["revision"])
    task = child(path, updated)
    with pytest.raises(ValueError, match="Only projects"):
        store.save(path, {"symbol": "star"}, task["id"], task["revision"])
