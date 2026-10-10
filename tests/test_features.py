import json
import sqlite3

import pytest

from organizer import store
from organizer.cli import main as cli
from organizer.reports import html_report
from tests.test_store import child


def define(path, root):
    return store.save(
        path,
        {
            "feature_definitions": {
                "ui": {"name": "UI development", "description": "Appearance"},
                "access": {"name": "Accessibility", "description": "Readable controls"},
            }
        },
        root["id"],
        root["revision"],
    )


def test_membership_is_shared_not_copied_or_counted_twice(workspace):
    path, root = workspace
    root = define(path, root)
    task = child(path, root, feature_ids=["ui", "access"])
    saved = store.save(path, {"status": "Done"}, task["id"], task["revision"])
    items, _ = store.load(path)
    assert len(items) == 2
    assert store.progress(items) == (1, 1)
    assert saved["parent_id"] == root["id"]
    assert store.ticket(saved) == store.ticket(task)
    assert set(store.features_for(saved, items)) == {"ui", "access"}
    assert "Features: UI development, Accessibility" in html_report(items)


def test_feature_rename_preserves_membership_and_project_rename_preserves_features(workspace):
    path, root = workspace
    root = define(path, root)
    task = child(path, root, feature_ids=["ui"])
    definitions = root["feature_definitions"]
    definitions["ui"]["name"] = "Interface"
    root = store.save(path, {"feature_definitions": definitions}, root["id"], root["revision"])
    root = store.save(path, {"project_key": "NEW"}, root["id"], root["revision"])
    items, _ = store.load(path)
    task = next(x for x in items if x["id"] == task["id"])
    assert task["feature_ids"] == ["ui"]
    assert store.features_for(task, items)["ui"]["name"] == "Interface"


def test_assigned_feature_removal_rejected_then_unassignment_allows_removal(workspace):
    path, root = workspace
    root = define(path, root)
    task = child(path, root, feature_ids=["ui"], status="Cancelled")
    with pytest.raises(ValueError, match="Remove their assignments"):
        store.save(path, {"feature_definitions": {}}, root["id"], root["revision"])
    assert store.load(path)[0][0] == root
    store.save(path, {"feature_ids": []}, task["id"], task["revision"])
    store.save(path, {"feature_definitions": {}}, root["id"], root["revision"])


@pytest.mark.parametrize(
    "fields",
    [
        {"feature_ids": ["missing"]},
        {"feature_ids": ["ui", "ui"]},
        {"feature_definitions": {"wrong": {"name": "Wrong"}}},
    ],
)
def test_invalid_work_item_features_do_not_write(workspace, fields):
    path, root = workspace
    root = define(path, root)
    before = store.load(path)
    with pytest.raises(ValueError):
        child(path, root, **fields)
    assert store.load(path) == before


@pytest.mark.parametrize(
    "definitions",
    [
        {"a": {"name": " "}},
        {"a": {"name": "UI"}, "b": {"name": " ui "}},
        {"bad:key": {"name": "Bad"}},
        {"a": {"name": "UI", "extra": True}},
    ],
)
def test_invalid_feature_definitions_rejected(workspace, definitions):
    path, root = workspace
    with pytest.raises(ValueError):
        store.save(path, {"feature_definitions": definitions}, root["id"], root["revision"])


def test_cross_project_assignment_and_project_membership_rejected(workspace):
    path, root = workspace
    root = define(path, root)
    other = store.save(path, {"kind": "Project", "project_key": "OTHER", "title": "Other"})
    with pytest.raises(ValueError, match="belong to this project"):
        child(path, other, feature_ids=["ui"])
    with pytest.raises(ValueError, match="not projects"):
        store.save(path, {"feature_ids": ["ui"]}, root["id"], root["revision"])


def test_features_roundtrip_copies_legacy_and_invalid_snapshots(workspace):
    path, root = workspace
    root = define(path, root)
    child(path, root, feature_ids=["ui", "access"])
    exported = store.export_snapshot(path)
    assert json.loads(exported)["version"] == 5
    store.import_snapshot(path, exported, new_key="COPY")
    items, _ = store.load(path)
    copied = next(x for x in items if x["project_key"] == "COPY" and x["kind"] == "Task")
    assert set(store.features_for(copied, items)) == {"ui", "access"}
    invalid = json.loads(exported)
    invalid["items"][1]["feature_ids"] = ["unknown"]
    with pytest.raises(ValueError):
        store.import_snapshot(path, json.dumps(invalid), new_key="INVALID")
    assert store.load(path)[0] == items
    legacy = json.loads(exported)
    legacy["version"] = 3
    for item in legacy["items"]:
        del item["feature_ids"], item["feature_definitions"]
    assert all(not x.feature_ids for x in store.parse_snapshot(json.dumps(legacy)).items)


def test_v5_migration_backs_up_before_adding_empty_features(workspace):
    path, root = workspace
    child(path, root)
    with sqlite3.connect(path) as db:
        db.execute("ALTER TABLE items DROP COLUMN feature_definitions")
        db.execute("ALTER TABLE items DROP COLUMN feature_ids")
        db.execute("PRAGMA user_version=5")
    store.initialize(path)
    store.initialize(path)
    assert all(not x["feature_ids"] and not x["feature_definitions"] for x in store.load(path)[0])
    backups = list(path.parent.glob("test.pre-v0.6.0-*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 5
        assert "feature_ids" not in {x[1] for x in db.execute("PRAGMA table_info(items)")}


def test_agent_feature_updates_use_same_validation_and_escape_reports(workspace, tmp_path, capsys):
    path, root = workspace
    root = define(path, root)
    task = child(path, root)
    update = tmp_path / "features.json"
    update.write_text(json.dumps({"feature_ids": ["ui", "access"]}))
    assert (
        cli(["--db", str(path), "update", store.ticket(task), "--revision", "1", "--file", str(update)]) == 0
    )
    result = json.loads(capsys.readouterr().out)["data"]
    assert set(result["features"]) == {"ui", "access"}
    definitions = root["feature_definitions"]
    definitions["ui"]["name"] = "<script>evil()</script>"
    store.save(path, {"feature_definitions": definitions}, root["id"], root["revision"])
    report = html_report(store.load(path)[0])
    assert "<script>" not in report
    assert "&lt;script&gt;" in report
