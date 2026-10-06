import json

import pytest

from organizer import store
from organizer.cli import main as cli
from organizer.reports import html_report


@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "test.db"
    store.initialize(path)
    root = store.save(path, {"kind": "Project", "project_key": "TEST", "title": "Test project"})
    return path, root


def child(path, parent, title="A task", **fields):
    return store.save(
        path,
        {
            "kind": "Task",
            "project_key": parent["project_key"],
            "parent_id": parent["id"],
            "title": title,
            **fields,
        },
    )


def test_project_stages_are_independent_from_task_progress(workspace):
    path, root = workspace
    assert root["status"] == "Still a Dream"
    child(path, root, status="Done")
    assert store.progress(store.load(path)[0]) == (1, 1)
    root = store.save(path, {"status": "Just Designing"}, root["id"], root["revision"])
    assert root["status"] == "Just Designing"
    with pytest.raises(ValueError, match="valid project status"):
        store.save(path, {"status": "Ready"}, root["id"], root["revision"])


def test_task_cannot_use_project_stage(workspace):
    path, root = workspace
    with pytest.raises(ValueError, match="valid task status"):
        child(path, root, status="Still a Dream")


def test_progress_avoids_parent_double_counting_and_excludes_ideas(workspace):
    path, root = workspace
    goal = child(path, root, kind="Major goal")
    task = child(path, goal, status="Done")
    child(path, task, kind="Subtask", status="Done")
    child(path, task, title="unfinished", kind="Subtask")
    child(path, root, kind="Idea")
    cancelled = child(path, root, kind="Major goal", status="Cancelled")
    child(path, cancelled, status="Done")
    assert store.progress(store.load(path)[0]) == (1, 2)


def test_reparent_cycle_and_cross_project_rejected(workspace):
    path, root = workspace
    task = child(path, root)
    sub = child(path, task, kind="Subtask")
    with pytest.raises(ValueError, match="higher level"):
        store.save(path, {"parent_id": sub["id"]}, task["id"], task["revision"])
    other = store.save(path, {"kind": "Project", "project_key": "OTHER", "title": "Other"})
    with pytest.raises(ValueError, match="same project"):
        store.save(path, {"parent_id": other["id"]}, task["id"], task["revision"])


def test_conflicting_agent_update_does_not_overwrite_newer_edit(workspace):
    path, root = workspace
    task = child(path, root)
    store.save(path, {"status": "Done"}, task["id"], task["revision"], actor="Codex")
    with pytest.raises(ValueError, match="another window"):
        store.save(path, {"status": "Ready"}, task["id"], task["revision"])
    assert next(x for x in store.load(path)[0] if x["id"] == task["id"])["status"] == "Done"
    assert store.activity(path, task["id"])[0]["actor"] == "Codex"


def test_snapshot_round_trip_with_repository_and_relationships(workspace, tmp_path):
    path, root = workspace
    store.save(path, {"repository_url": "https://github.com/example/test"}, root["id"], root["revision"])
    a, b = child(path, root, "A"), child(path, root, "B")
    store.add_link(path, a["id"], b["id"], "blocks")
    target = tmp_path / "imported.db"
    store.initialize(target)
    assert store.import_snapshot(target, store.export_snapshot(path)) == 3
    items, links = store.load(target)
    assert len(links) == 1
    assert (
        next(x for x in items if x["kind"] == "Project")["repository_url"]
        == "https://github.com/example/test"
    )
    assert a["id"] not in {x["id"] for x in items}
    assert sorted(store.ticket(x) for x in items) == ["TEST-0001", "TEST-0002", "TEST-0003"]


def test_import_collisions_rejected_without_partial_write(workspace):
    path, root = workspace
    child(path, root)
    raw = store.export_snapshot(path)
    with pytest.raises(ValueError, match="already exists"):
        store.import_snapshot(path, raw)
    assert len(store.load(path)[0]) == 2
    store.import_snapshot(path, raw, new_key="COPY")
    assert len(store.load(path)[0]) == 4


def test_malformed_snapshot_is_atomic(workspace):
    path, _ = workspace
    raw = json.loads(store.export_snapshot(path))
    raw["items"][0]["parent_id"] = "missing"
    with pytest.raises(ValueError):
        store.import_snapshot(path, json.dumps(raw), new_key="COPY")
    assert len(store.load(path)[0]) == 1


def test_cross_project_export_reports_omitted_links(workspace):
    path, root = workspace
    other = store.save(path, {"kind": "Project", "project_key": "OTHER", "title": "Other"})
    store.add_link(path, root["id"], other["id"], "relates to")
    snapshot = store.parse_snapshot(store.export_snapshot(path, "TEST"))
    assert snapshot.omitted_external_links == 1
    assert not snapshot.links
    assert len(store.parse_snapshot(store.export_snapshot(path)).links) == 1


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "https://name:secret@github.com/repo",
        "file:///C:/secret",
        "http://github.com/repo",
    ],
)
def test_invalid_repository_links_rejected(workspace, url):
    path, root = workspace
    with pytest.raises(ValueError, match="HTTPS"):
        store.save(path, {"repository_url": url}, root["id"], root["revision"])


def test_report_escapes_project_content(workspace):
    path, root = workspace
    child(path, root, title='<script>alert("no")</script>', description='<img src=x onerror="alert(1)">')
    report = html_report(store.load(path)[0])
    assert "<script>" not in report
    assert "<img" not in report
    assert "&lt;script&gt;" in report


def test_backup_can_be_opened_and_edited_independently(workspace, tmp_path):
    path, root = workspace
    destination = tmp_path / "backup.db"
    store.backup(path, destination)
    store.initialize(destination)
    copy = store.load(destination)[0][0]
    store.save(destination, {"title": "Backup edit"}, copy["id"], copy["revision"])
    assert store.load(path)[0][0]["title"] == root["title"]


def test_cli_get_update_and_stale_error_are_json(workspace, tmp_path, capsys):
    path, root = workspace
    assert cli(["--db", str(path), "get", "TEST-0001"]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["revision"] == 1
    patch = tmp_path / "update.json"
    patch.write_text(json.dumps({"status": "In Progress"}), encoding="utf-8")
    args = [
        "--db",
        str(path),
        "--actor",
        "Test agent",
        "update",
        "TEST-0001",
        "--revision",
        "1",
        "--file",
        str(patch),
    ]
    assert cli(args) == 0
    assert json.loads(capsys.readouterr().out)["data"]["status"] == "In Progress"
    assert cli(args) == 1
    assert not json.loads(capsys.readouterr().out)["ok"]


def test_duplicate_undirected_relationship_rejected(workspace):
    path, root = workspace
    a, b = child(path, root, "A"), child(path, root, "B")
    store.add_link(path, a["id"], b["id"], "relates to")
    with pytest.raises(ValueError, match="already exists"):
        store.add_link(path, b["id"], a["id"], "relates to")


def test_tags_normalized_and_ids_stable(workspace):
    path, root = workspace
    item = child(path, root, tags=[" Design ", "design", "", "Color"])
    assert item["tags"] == ["design", "color"]
    updated = store.save(path, {"status": "Done"}, item["id"], item["revision"])
    assert store.ticket(item) == store.ticket(updated)
    assert child(path, root)["number"] == 3


def test_project_key_change_is_rejected_by_shared_store(workspace):
    path, root = workspace
    with pytest.raises(ValueError, match="cannot change"):
        store.save(path, {"project_key": "CHANGED"}, root["id"], root["revision"])
    assert store.load(path)[0][0]["project_key"] == "TEST"


@pytest.mark.parametrize("parent", [123, ["TEST-0001"], {"ticket": "TEST-0001"}])
def test_cli_invalid_parent_returns_json_error(workspace, tmp_path, capsys, parent):
    path, _ = workspace
    payload = tmp_path / "invalid.json"
    payload.write_text(
        json.dumps({"kind": "Task", "project_key": "TEST", "title": "Invalid", "parent_id": parent}),
        encoding="utf-8",
    )
    assert cli(["--db", str(path), "create", "--file", str(payload)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert not result["ok"]
    assert "references" in result["error"]
    assert len(store.load(path)[0]) == 1


def test_backup_rejects_working_database_as_destination(workspace):
    path, _ = workspace
    with pytest.raises(ValueError, match="different"):
        store.backup(path, path)
    assert len(store.load(path)[0]) == 1
