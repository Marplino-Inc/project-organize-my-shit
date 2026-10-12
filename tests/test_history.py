import pytest

from organizer import history, store
from tests.test_store import child


def edit(path, item, fields):
    current = next(x for x in store.load(path)[0] if x["id"] == item["id"])
    return store.save(path, fields, current["id"], current["revision"], record_history=True)


def move(path, direction):
    entries = [x for x in history.state(path) if x["applied"] == (direction == "undo")]
    history.apply(path, direction, (entries[-1] if direction == "undo" else entries[0])["id"])


def get(path, item):
    return next(x for x in store.load(path)[0] if x["id"] == item["id"])


def test_five_steps_redo_branch_noop_and_creation(workspace):
    path, root = workspace
    task = child(path, root)
    assert history.state(path) == []
    for i in range(7):
        edit(path, task, {"title": str(i)})
    assert len(history.state(path)) == 5
    edit(path, task, {"title": "6"})
    assert len(history.state(path)) == 5
    for _ in range(5):
        move(path, "undo")
    assert get(path, task)["title"] == "1"
    child(path, root, title="Keep this new task")
    for _ in range(5):
        move(path, "redo")
    assert get(path, task)["title"] == "6"
    move(path, "undo")
    edit(path, task, {"title": "New direction"})
    assert all(entry["applied"] for entry in history.state(path))
    assert len(store.load(path)[0]) == 3
    assert get(path, task)["revision"] > task["revision"]


def test_external_edits_preserved_or_conflict_atomically(workspace):
    path, root = workspace
    task = child(path, root)
    task = edit(path, task, {"title": "UI title", "status": "Done"})
    task = store.save(path, {"description": "Agent notes"}, task["id"], task["revision"], actor="Agent")
    move(path, "undo")
    assert get(path, task)["description"] == "Agent notes"
    move(path, "redo")
    task = get(path, task)
    store.save(path, {"status": "Ready"}, task["id"], task["revision"], actor="Agent")
    before = store.load(path)
    with pytest.raises(ValueError, match="outside UI history"):
        move(path, "undo")
    assert store.load(path) == before
    assert len(history.state(path)) == 1


def test_definitions_excluded_and_memberships_tags_reversible(workspace):
    path, root = workspace
    root = edit(
        path, root, {"feature_definitions": {"ui": {"name": "UI"}}, "tag_defaults": {"release": None}}
    )
    assert history.state(path) == []
    task = child(path, root)
    edit(path, task, {"feature_ids": ["ui"], "tags": {"release": "1.2"}})
    move(path, "undo")
    assert get(path, task)["tags"] == {}
    assert get(path, task)["feature_ids"] == []
    move(path, "redo")
    assert get(path, task)["feature_ids"] == ["ui"]
    assert get(path, task)["tags"] == {"release": "1.2"}
    edit(
        path,
        root,
        {
            "title": "Changed",
            "feature_definitions": {"ui": {"name": "UI"}, "new": {"name": "New"}},
            "tag_defaults": {"release": None, "new": None},
        },
    )
    move(path, "undo")
    assert "new" in get(path, root)["feature_definitions"]
    assert "new" in get(path, root)["tag_defaults"]
    assert get(path, root)["title"] == root["title"]


def test_rename_with_new_children_and_stale_history(workspace):
    path, root = workspace
    root = edit(path, root, {"project_key": "NEW"})
    task = child(path, root)
    entry = history.state(path)[0]
    move(path, "undo")
    assert {x["project_key"] for x in store.load(path)[0]} == {"TEST"}
    with pytest.raises(ValueError, match="History changed"):
        history.apply(path, "undo", entry["id"])
    move(path, "redo")
    assert get(path, task)["project_key"] == "NEW"
    assert store.activity(path, root["id"])[0]["action"] == "redo"


def test_invalid_parent_change_rolls_back(workspace):
    path, root = workspace
    parent = child(path, root)
    parent = edit(path, parent, {"kind": "Major goal"})
    child(path, parent)
    before = store.load(path)
    with pytest.raises(ValueError, match="higher level"):
        move(path, "undo")
    assert store.load(path) == before
