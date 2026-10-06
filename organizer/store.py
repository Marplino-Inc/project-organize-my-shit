"""Persistence and rules. UI handlers call these functions; SQL stays here."""

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

STATUSES = ("Backlog", "Ready", "In progress", "Done", "Cancelled")
PROJECT_STATUSES = ("Still a Dream", "Just Designing", "In Progress", "On Hold", "Completed", "Cancelled")
KINDS = ("Project", "Major goal", "Minor goal", "Task", "Subtask", "Idea")
COLORS = {"Violet": "#8b70ef", "Teal": "#24a99a", "Amber": "#d99a30", "Coral": "#ed7d75", "Blue": "#6299e8"}
RANK = {"Project": 0, "Major goal": 1, "Minor goal": 2, "Task": 3, "Subtask": 4, "Idea": 4}
EFFORT = {None: "Not estimated", 1: "XS", 2: "S", 3: "M", 4: "L", 5: "XL"}


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=80)
    project_key: str = Field(pattern=r"^[A-Z][A-Z0-9]{1,9}$")
    number: int = Field(ge=1)
    parent_id: str | None = None
    kind: Literal["Project", "Major goal", "Minor goal", "Task", "Subtask", "Idea"]
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=30000)
    status: Literal[
        "Backlog",
        "Ready",
        "In progress",
        "Done",
        "Cancelled",
        "Still a Dream",
        "Just Designing",
        "In Progress",
        "On Hold",
        "Completed",
    ] = "Backlog"
    effort: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=30)
    color: Literal["Violet", "Teal", "Amber", "Coral", "Blue"] = "Violet"
    blocked: str = Field(default="", max_length=1000)
    repository_url: str = Field(default="", max_length=2000)
    created_at: str
    updated_at: str
    revision: int = Field(default=1, ge=1)


class Link(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source: str
    target: str
    kind: Literal["blocks", "relates to"]


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    format: Literal["organize-snapshot"] = "organize-snapshot"
    version: Literal[1] = 1
    exported_at: str
    items: list[Item] = Field(max_length=10000)
    links: list[Link] = Field(max_length=30000)
    omitted_external_links: int = Field(default=0, ge=0)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ticket(item):
    return f"{item['project_key']}-{item['number']:04d}"


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


@contextmanager
def transaction(path):
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with transaction(path) as db:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > 3:
            raise ValueError("This database needs a newer version of Organize.")
        db.execute("""CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY, project_key TEXT NOT NULL, number INTEGER NOT NULL,
            parent_id TEXT REFERENCES items(id), kind TEXT NOT NULL, title TEXT NOT NULL,
            description TEXT NOT NULL, status TEXT NOT NULL, effort INTEGER,
            tags TEXT NOT NULL, color TEXT NOT NULL, blocked TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, revision INTEGER NOT NULL,
            repository_url TEXT NOT NULL DEFAULT '',
            UNIQUE(project_key, number))""")
        db.execute("CREATE INDEX IF NOT EXISTS items_parent ON items(parent_id)")
        db.execute("""CREATE TABLE IF NOT EXISTS links (
            source TEXT REFERENCES items(id), target TEXT REFERENCES items(id), kind TEXT NOT NULL,
            PRIMARY KEY(source, target, kind))""")
        db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        if version == 1:
            db.execute("ALTER TABLE items ADD COLUMN repository_url TEXT NOT NULL DEFAULT ''")
        db.execute("""CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY, item_id TEXT NOT NULL, actor TEXT NOT NULL,
            action TEXT NOT NULL, timestamp TEXT NOT NULL, fields TEXT NOT NULL)""")
        if version in (1, 2):
            for before, after in (
                ("Backlog", "Still a Dream"),
                ("Ready", "Just Designing"),
                ("In progress", "In Progress"),
                ("Done", "Completed"),
            ):
                db.execute("UPDATE items SET status=? WHERE kind='Project' AND status=?", (after, before))
        db.execute("PRAGMA user_version=3")


def read_items(db):
    items = [dict(row) for row in db.execute("SELECT * FROM items ORDER BY project_key, number")]
    for item in items:
        item["tags"] = json.loads(item["tags"])
    return items


def load(path):
    with transaction(path) as db:
        return read_items(db), [dict(row) for row in db.execute("SELECT * FROM links")]


def setting(path, key, default=None):
    with transaction(path) as db:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default


def set_setting(path, key, value):
    with transaction(path) as db:
        db.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))


def validate_graph(items, links):
    by_id = {item["id"]: item for item in items}
    if len(by_id) != len(items):
        raise ValueError("Duplicate internal IDs in the snapshot.")
    projects = {}
    keys = set()
    for item in items:
        Item.model_validate(item)
        allowed_statuses = PROJECT_STATUSES if item["kind"] == "Project" else STATUSES
        if item["status"] not in allowed_statuses:
            raise ValueError(f"Choose a valid {item['kind'].lower()} status: {', '.join(allowed_statuses)}.")
        if not item["title"].strip():
            raise ValueError("A title cannot be blank.")
        if item["repository_url"]:
            url = urlparse(item["repository_url"])
            if (
                item["kind"] != "Project"
                or url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
            ):
                raise ValueError("Repository links must be HTTPS URLs without credentials, on projects only.")
        if any(not tag.strip() or len(tag) > 40 for tag in item["tags"]):
            raise ValueError("Tags must contain 1–40 characters.")
        key = (item["project_key"], item["number"])
        if key in keys:
            raise ValueError("Duplicate ticket numbers in a project.")
        keys.add(key)
        if item["kind"] == "Project":
            if item["parent_id"] or item["project_key"] in projects:
                raise ValueError("Each project needs one root and a unique project key.")
            projects[item["project_key"]] = item["id"]
    for item in items:
        if item["project_key"] not in projects:
            raise ValueError("Every item must belong to an included project.")
        if item["kind"] != "Project":
            parent = by_id.get(item["parent_id"])
            if not parent or parent["project_key"] != item["project_key"]:
                raise ValueError("Choose a parent in the same project.")
            if RANK[parent["kind"]] >= RANK[item["kind"]]:
                raise ValueError("A parent must be a higher level than its child.")
        if item["effort"] is not None and item["kind"] in ("Project", "Major goal"):
            raise ValueError("Estimate minor goals, tasks, subtasks, or ideas.")
    seen = set()
    for link in links:
        Link.model_validate(link)
        if link["source"] not in by_id or link["target"] not in by_id:
            raise ValueError("A relationship points to a missing item.")
        if link["source"] == link["target"]:
            raise ValueError("An item cannot link to itself.")
        pair = (link["source"], link["target"])
        if link["kind"] == "relates to":
            pair = tuple(sorted(pair))
        identity = (*pair, link["kind"])
        if identity in seen:
            raise ValueError("This relationship already exists.")
        seen.add(identity)


def write_item(db, item):
    row = {**item, "tags": json.dumps(item["tags"])}
    columns = ",".join(row)
    markers = ",".join("?" for _ in row)
    # Only validated Item fields become column names. Values are always parameters.
    db.execute(f"INSERT INTO items ({columns}) VALUES ({markers})", tuple(row.values()))


def save(path, fields, item_id=None, revision=None, actor="You"):
    editable = {
        "project_key",
        "parent_id",
        "kind",
        "title",
        "description",
        "status",
        "effort",
        "tags",
        "color",
        "blocked",
        "repository_url",
    }
    if set(fields) - editable:
        raise ValueError("Unknown or read-only fields: " + ", ".join(sorted(set(fields) - editable)))
    if not actor.strip() or len(actor) > 100:
        raise ValueError("Actor must contain 1–100 characters.")
    with transaction(path) as db:
        items = read_items(db)
        existing = next((x for x in items if x["id"] == item_id), None)
        if item_id and (existing is None or existing["revision"] != revision):
            raise ValueError("This item changed in another window. Close and reopen it before saving.")
        stamp = now()
        if existing:
            fixed = {key: existing[key] for key in ("id", "project_key", "number", "created_at")}
            item = {**existing, **fields, **fixed, "updated_at": stamp, "revision": revision + 1}
            if fields.get("kind", existing["kind"]) == "Project" and existing["kind"] != "Project":
                raise ValueError("Create a new project using New project.")
            if existing["kind"] == "Project" and item["kind"] != "Project":
                raise ValueError("A project must remain a project.")
        else:
            if fields.get("kind") == "Project" and "status" not in fields:
                fields = {**fields, "status": "Still a Dream"}
            raw_key = fields.get("project_key", "")
            if not isinstance(raw_key, str):
                raise ValueError("Project key must be a string.")
            project_key = raw_key.strip().upper()
            if fields.get("kind") == "Project" and any(x["project_key"] == project_key for x in items):
                raise ValueError("That project key is already in use. Choose another.")
            number = max((x["number"] for x in items if x["project_key"] == project_key), default=0) + 1
            item = Item.model_validate(
                {
                    **fields,
                    "id": str(uuid4()),
                    "project_key": project_key,
                    "number": number,
                    "created_at": stamp,
                    "updated_at": stamp,
                }
            ).model_dump()
        item = Item.model_validate(item).model_dump()
        item["title"] = item["title"].strip()
        item["tags"] = list(dict.fromkeys(tag.strip().lower() for tag in item["tags"] if tag.strip()))
        combined = [x for x in items if x["id"] != item["id"]] + [item]
        links = [dict(row) for row in db.execute("SELECT * FROM links")]
        validate_graph(combined, links)
        if existing:
            row = {**item, "tags": json.dumps(item["tags"])}
            db.execute(
                "UPDATE items SET " + ",".join(f"{k}=?" for k in row) + " WHERE id=?",
                (*row.values(), item["id"]),
            )
        else:
            write_item(db, item)
        changed = sorted(k for k in fields if not existing or existing[k] != item[k])
        db.execute(
            "INSERT INTO activity(item_id, actor, action, timestamp, fields) VALUES (?, ?, ?, ?, ?)",
            (item["id"], actor, "updated" if existing else "created", stamp, json.dumps(changed)),
        )
        return item


def activity(path, item_id):
    with transaction(path) as db:
        return [
            dict(row)
            for row in db.execute(
                "SELECT actor, action, timestamp, fields FROM activity WHERE item_id=? ORDER BY id DESC LIMIT 20",
                (item_id,),
            )
        ]


def add_link(path, source, target, kind):
    with transaction(path) as db:
        link = {"source": source, "target": target, "kind": kind}
        links = [dict(row) for row in db.execute("SELECT * FROM links")]
        validate_graph(read_items(db), links + [link])
        db.execute("INSERT INTO links VALUES (?, ?, ?)", (source, target, kind))


def remove_link(path, link):
    with transaction(path) as db:
        db.execute(
            "DELETE FROM links WHERE source=? AND target=? AND kind=?",
            (link["source"], link["target"], link["kind"]),
        )


def active_leaves(items):
    """Only committed terminal work counts. Cancelled ancestors exclude their subtree."""
    by_id = {item["id"]: item for item in items}
    eligible = []
    for item in items:
        cursor = item
        excluded = item["kind"] in ("Project", "Idea")
        while cursor:
            if cursor["status"] == "Cancelled" or cursor["kind"] == "Idea":
                excluded = True
            cursor = by_id.get(cursor["parent_id"])
        if not excluded:
            eligible.append(item)
    parents = {x["parent_id"] for x in eligible}
    return [x for x in eligible if x["id"] not in parents]


def progress(items):
    leaves = active_leaves(items)
    done = sum(item["status"] == "Done" for item in leaves)
    return done, len(leaves)


def export_snapshot(path, project_key=None):
    items, links = load(path)
    if project_key:
        items = [x for x in items if x["project_key"] == project_key]
    ids = {x["id"] for x in items}
    included = [x for x in links if x["source"] in ids and x["target"] in ids]
    omitted = sum((x["source"] in ids) != (x["target"] in ids) for x in links)
    return Snapshot(
        exported_at=now(),
        items=[Item(**x) for x in items],
        links=[Link(**x) for x in included],
        omitted_external_links=omitted,
    ).model_dump_json(indent=2)


def parse_snapshot(raw):
    if len(raw) > 10_000_000:
        raise ValueError("Snapshot exceeds the 10 MB limit.")
    snapshot = Snapshot.model_validate_json(raw)
    if not snapshot.items:
        raise ValueError("The snapshot contains no projects.")
    validate_graph([x.model_dump() for x in snapshot.items], [x.model_dump() for x in snapshot.links])
    return snapshot


def import_snapshot(path, raw, new_key=None):
    snapshot = parse_snapshot(raw)
    items = [x.model_dump() for x in snapshot.items]
    links = [x.model_dump() for x in snapshot.links]
    keys = {x["project_key"] for x in items}
    if new_key:
        if len(keys) != 1:
            raise ValueError("A replacement key is only available for a single-project snapshot.")
        new_key = new_key.strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", new_key):
            raise ValueError("Project keys need 2–10 letters/numbers, starting with a letter.")
        for item in items:
            item["project_key"] = new_key
        keys = {new_key}
    # Import a separate copy with new internal identities, retaining the human ticket numbers.
    ids = {x["id"]: str(uuid4()) for x in items}
    for item in items:
        item["id"] = ids[item["id"]]
        item["parent_id"] = ids.get(item["parent_id"])
        item["revision"] = 1
    for link in links:
        link["source"], link["target"] = ids[link["source"]], ids[link["target"]]
    with transaction(path) as db:
        existing = read_items(db)
        collisions = keys & {x["project_key"] for x in existing}
        if collisions:
            raise ValueError(
                "Project key already exists: " + ", ".join(sorted(collisions)) + ". Import with a new key."
            )
        validate_graph(existing + items, links)
        for item in sorted(items, key=lambda x: RANK[x["kind"]]):
            write_item(db, item)
        db.executemany(
            "INSERT INTO links VALUES (?, ?, ?)", [(x["source"], x["target"], x["kind"]) for x in links]
        )
    return len(items)


def backup(path, destination):
    with connect(path) as source, sqlite3.connect(destination) as target:
        source.backup(target)
