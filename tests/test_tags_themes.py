import json
import sqlite3

import pytest

from organizer import store, themes
from organizer.cli import main as cli
from organizer.reports import html_report
from tests.test_store import child


def test_inheritance_updates_overrides_null_and_reset(workspace):
    path, root = workspace
    task = child(path, root)
    custom = child(path, root, tags={"owner": None, "area": "UI"})
    root = store.save(path, {"tag_defaults": {"owner": "Gary", "release": None}}, root["id"], 1)
    items, _ = store.load(path)
    assert store.effective_tags(root, items) == {"owner": "Gary", "release": None}
    assert store.effective_tags(task, items) == {"owner": "Gary", "release": None}
    assert store.effective_tags(custom, items) == {"owner": None, "release": None, "area": "UI"}
    store.save(path, {"tag_defaults": {"owner": "Agent"}}, root["id"], root["revision"])
    items, _ = store.load(path)
    assert store.effective_tags(task, items) == {"owner": "Agent"}
    assert store.effective_tags(custom, items)["owner"] is None
    custom = store.save(path, {"tags": {}}, custom["id"], custom["revision"])
    assert store.effective_tags(custom, items) == {"owner": "Agent"}
    assert task["revision"] == next(x for x in items if x["id"] == task["id"])["revision"]


@pytest.mark.parametrize(
    "tags",
    [
        {"": "x"},
        {"a": " "},
        {"a": 1},
        {"a": False},
        {"a": []},
        {"A": "x", " a ": "y"},
        ["old"],
        {"a" * 41: None},
        {"a": "x" * 201},
    ],
)
def test_invalid_pairs_rejected(workspace, tags):
    path, root = workspace
    with pytest.raises(ValueError):
        child(path, root, tags=tags)
    assert len(store.load(path)[0]) == 1


def test_default_tags_only_on_projects(workspace):
    path, root = workspace
    with pytest.raises(ValueError, match="Only projects"):
        child(path, root, tag_defaults={"owner": None})


def test_legacy_database_migration_backup_and_idempotence(workspace):
    path, root = workspace
    task = child(path, root, description="Keep my notes", status="Done")
    store.set_setting(path, "theme", "Dark")
    store.add_link(path, root["id"], task["id"], "relates to")
    with sqlite3.connect(path) as db:
        db.execute("ALTER TABLE items DROP COLUMN tag_defaults")
        db.execute("UPDATE items SET tags=? WHERE id=?", (json.dumps(["legacy"]), root["id"]))
        db.execute("UPDATE items SET tags=? WHERE id=?", (json.dumps(["local"]), task["id"]))
        db.execute("PRAGMA user_version=3")
    store.initialize(path)
    store.initialize(path)
    items, links = store.load(path)
    migrated = next(x for x in items if x["id"] == task["id"])
    assert migrated == {**task, "tags": {"local": None}}
    assert store.effective_tags(migrated, items) == {"legacy": None, "local": None}
    assert len(links) == 1
    assert store.setting(path, "theme") == "Dark"
    backups = list(path.parent.glob("test.pre-v0.2.0-*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 3
        assert json.loads(db.execute("SELECT tags FROM items WHERE id=?", (root["id"],)).fetchone()[0]) == [
            "legacy"
        ]


@pytest.mark.parametrize("version", [1, 2])
def test_snapshot_versions_preserve_tags(workspace, tmp_path, version):
    path, root = workspace
    child(path, root, tags={"owner": None})
    root = store.save(path, {"tag_defaults": {"owner": "Gary", "release": None}}, root["id"], 1)
    raw = json.loads(store.export_snapshot(path))
    if version == 1:
        raw["version"] = 1
        for item in raw["items"]:
            item["tags"] = list(item["tag_defaults"] if item["kind"] == "Project" else item["tags"])
            del item["tag_defaults"]
    target = tmp_path / "import.db"
    store.initialize(target)
    store.import_snapshot(target, json.dumps(raw))
    items, _ = store.load(target)
    project = next(x for x in items if x["kind"] == "Project")
    assert project["tag_defaults"] == {"owner": "Gary" if version == 2 else None, "release": None}
    assert store.effective_tags(next(x for x in items if x["kind"] == "Task"), items) == {
        "owner": None,
        "release": None,
    }


def test_cli_filter_options_and_report_use_effective_pairs(workspace, capsys):
    path, root = workspace
    store.save(path, {"tag_defaults": {"owner": "<Gary>", "release": None}}, root["id"], 1)
    task = child(path, root, tags={"release": "(null)"})
    assert cli(["--db", str(path), "get", store.ticket(task)]) == 0
    result = json.loads(capsys.readouterr().out)["data"]
    assert result["tags"] == {"release": "(null)"}
    assert result["effective_tags"] == {"owner": "<Gary>", "release": "(null)"}
    items, _ = store.load(path)
    options = store.tag_options(items)
    assert json.dumps(["release", None]) in options
    assert json.dumps(["release", "(null)"]) in options
    assert "owner: &lt;Gary&gt;" in html_report(items)


@pytest.mark.parametrize("items", [None, 123])
def test_malformed_legacy_snapshot_returns_validation_error(items):
    with pytest.raises(ValueError, match="must be a list"):
        store.parse_snapshot(json.dumps({"version": 1, "items": items}))


def contrast(first, second):
    def luminance(color):
        values = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    low, high = sorted([luminance(first), luminance(second)])
    return (high + 0.05) / (low + 0.05)


@pytest.mark.parametrize("family", themes.FAMILIES)
@pytest.mark.parametrize("mode", ["light", "dark"])
def test_theme_text_and_buttons_have_aa_contrast(family, mode):
    tokens = dict(zip(themes.TOKEN_NAMES, themes.FAMILIES[family][mode]))
    for foreground in ("text", "muted", "accent"):
        for background in ("canvas", "surface", "surface-soft", "accent-soft"):
            assert contrast(tokens[foreground], tokens[background]) >= 4.5, (
                family,
                mode,
                foreground,
                background,
            )
    assert contrast("#ffffff", tokens["button"]) >= 4.5
