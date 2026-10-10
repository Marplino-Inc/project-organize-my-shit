import json

import pytest

from organizer import store
from organizer.cli import main as cli
from organizer.reports import html_report
from tests.test_store import child


def test_rename_updates_all_levels_preserving_identity_links_and_defaults(workspace):
    path, root = workspace
    root = store.save(path, {"tag_defaults": {"owner": "Gary"}}, root["id"], root["revision"])
    parent = root
    for kind in ("Major goal", "Minor goal", "Task", "Subtask"):
        parent = child(path, parent, kind=kind, status="Cancelled")
    child(path, root, kind="Idea")
    other = store.save(path, {"kind": "Project", "project_key": "OTHER", "title": "Other"})
    store.add_link(path, parent["id"], other["id"], "relates to")
    before, links = store.load(path)
    saved = store.save(path, {"project_key": " renamed "}, root["id"], root["revision"], actor="Rename test")
    assert saved["project_key"] == "RENAMED"
    after, after_links = store.load(path)
    assert links == after_links
    for old in before:
        new = next(x for x in after if x["id"] == old["id"])
        if old["project_key"] == "OTHER":
            assert new == old
            continue
        assert new["project_key"] == "RENAMED"
        assert new["number"] == old["number"]
        assert new["revision"] == old["revision"] + 1
        assert new["parent_id"] == old["parent_id"]
        assert store.effective_tags(new, after) == {"owner": "Gary"}
        assert store.activity(path, new["id"])[0]["actor"] == "Rename test"
    assert child(path, saved)["number"] == 7
    with pytest.raises(ValueError, match="changed in another window"):
        store.save(path, {"title": "Stale edit"}, parent["id"], parent["revision"])
    assert "TEST-" not in html_report(after)
    assert all(x.project_key != "TEST" for x in store.parse_snapshot(store.export_snapshot(path)).items)


@pytest.mark.parametrize("new_key", ["OTHER", "?bad", "", None])
def test_invalid_rename_rolls_back_every_item_and_activity(workspace, new_key):
    path, root = workspace
    task = child(path, root)
    store.save(path, {"kind": "Project", "project_key": "OTHER", "title": "Other"})
    before = store.load(path)
    activity = store.activity(path, task["id"])
    with pytest.raises(ValueError):
        store.save(path, {"project_key": new_key}, root["id"], root["revision"])
    assert store.load(path) == before
    assert store.activity(path, task["id"]) == activity


def test_work_item_cannot_rename_or_move_project(workspace):
    path, root = workspace
    task = child(path, root)
    with pytest.raises(ValueError, match="on the project"):
        store.save(path, {"project_key": "OTHER"}, task["id"], task["revision"])


def test_cli_rename_accepts_uuid_and_old_labels_stop_resolving(workspace, tmp_path, capsys):
    path, root = workspace
    task = child(path, root)
    fields = tmp_path / "rename.json"
    fields.write_text(json.dumps({"project_key": "NEW"}))
    assert cli(["--db", str(path), "update", "TEST-0001", "--revision", "1", "--file", str(fields)]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["project_key"] == "NEW"
    assert cli(["--db", str(path), "get", "TEST-0002"]) == 1
    capsys.readouterr()
    assert cli(["--db", str(path), "get", task["id"]]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["project_key"] == "NEW"
    assert cli(["--db", str(path), "get", "NEW-0002"]) == 0
