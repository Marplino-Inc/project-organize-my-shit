"""Five persisted UI edit steps, applied as conflict-checked field patches."""

import json
from copy import deepcopy
from uuid import uuid4

KEY = "_ui_edit_history"
LIMIT = 5
MAP_FIELDS = {"tags", "tag_defaults", "feature_definitions"}
IGNORED = {"id", "number", "created_at", "updated_at", "revision"}


def read(db):
    row = db.execute("SELECT value FROM settings WHERE key=?", (KEY,)).fetchone()
    return json.loads(row[0]) if row else []


def write(db, entries):
    db.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (KEY, json.dumps(entries)))


def record(db, before, after, actor):
    changes = []
    for field in before.keys() - IGNORED:
        if before[field] == after[field]:
            continue
        if field in MAP_FIELDS:
            for key in sorted(before[field].keys() | after[field].keys()):
                # Defining new project tags/features is outside edit history.
                if key not in before[field] and field in {"tag_defaults", "feature_definitions"}:
                    continue
                old = [key in before[field], before[field].get(key)]
                new = [key in after[field], after[field].get(key)]
                if old != new:
                    changes.append({"field": field, "key": key, "before": old, "after": new})
        else:
            changes.append({"field": field, "before": before[field], "after": after[field]})
    if not changes:
        return
    entries = [entry for entry in read(db) if entry["applied"]]
    entries.append(
        {
            "id": str(uuid4()),
            "item_id": after["id"],
            "title": after["title"],
            "ticket": f"{after['project_key']}-{after['number']:04d}",
            "actor": actor,
            "changes": sorted(changes, key=lambda change: (change["field"], change.get("key", ""))),
            "applied": True,
        }
    )
    write(db, entries[-LIMIT:])


def state(path):
    from . import store

    with store.transaction(path) as db:
        return read(db)


def apply(path, direction, entry_id):
    from . import store

    if direction not in {"undo", "redo"}:
        raise ValueError("Choose undo or redo.")
    with store.transaction(path) as db:
        entries = read(db)
        candidates = [entry for entry in entries if entry["applied"] == (direction == "undo")]
        entry = (candidates[-1] if direction == "undo" else candidates[0]) if candidates else None
        if not entry or entry["id"] != entry_id:
            raise ValueError("History changed. Reopen history before continuing.")
        items = store.read_items(db)
        original = next((item for item in items if item["id"] == entry["item_id"]), None)
        if not original:
            raise ValueError("This item no longer exists.")
        updated = deepcopy(original)
        source, target = ("after", "before") if direction == "undo" else ("before", "after")
        for change in entry["changes"]:
            field = change["field"]
            if "key" in change:
                key = change["key"]
                current = [key in updated[field], updated[field].get(key)]
                if current != change[source]:
                    raise ValueError("This field changed outside UI history. No changes were applied.")
                present, value = change[target]
                if present:
                    updated[field][key] = value
                else:
                    updated[field].pop(key, None)
            else:
                if updated[field] != change[source]:
                    raise ValueError("This field changed outside UI history. No changes were applied.")
                updated[field] = change[target]
        replacements = {updated["id"]: updated}
        # Rename the whole current project, including work created after the original edit.
        if updated["project_key"] != original["project_key"]:
            if any(item["project_key"] == updated["project_key"] for item in items):
                raise ValueError("That project key is now in use. No changes were applied.")
            replacements.update(
                {
                    item["id"]: {**item, "project_key": updated["project_key"]}
                    for item in items
                    if item["project_key"] == original["project_key"] and item["id"] != updated["id"]
                }
            )
        combined = [replacements.get(item["id"], item) for item in items]
        links = [dict(row) for row in db.execute("SELECT * FROM links")]
        store.validate_graph(combined, links)
        stamp = store.now()
        for item in replacements.values():
            item["revision"] += 1
            item["updated_at"] = stamp
            row = store.storage_row(store.Item.model_validate(item).model_dump())
            db.execute(
                "UPDATE items SET " + ",".join(f"{key}=?" for key in row) + " WHERE id=?",
                (*row.values(), item["id"]),
            )
            fields = (
                [change["field"] for change in entry["changes"]]
                if item["id"] == updated["id"]
                else ["project_key"]
            )
            db.execute(
                "INSERT INTO activity(item_id, actor, action, timestamp, fields) VALUES (?, ?, ?, ?, ?)",
                (item["id"], "You", direction, stamp, json.dumps(sorted(set(fields)))),
            )
        entry["applied"] = direction == "redo"
        write(db, entries)


def summary(entry):
    descriptions = []
    for change in entry["changes"]:
        label = change["field"].replace("_", " ").capitalize()
        if "key" in change:
            label += ": " + change["key"]

        def preview(value):
            if "key" in change:
                present, value = value
                if not present:
                    return "not set"
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            return text[:70] + ("..." if len(text) > 70 else "")

        label += f": {preview(change['before'])} -> {preview(change['after'])}"
        descriptions.append(label)
    return "; ".join(descriptions)
