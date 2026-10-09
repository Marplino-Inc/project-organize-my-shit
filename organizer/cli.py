"""Machine-readable agent interface, using exactly the same validation as the UI."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import store
from .config import database_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=database_path())
    parser.add_argument("--actor", default="Agent", help="Name shown in item activity")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema", help="Item JSON schema and editable fields")
    commands.add_parser("projects")
    listing = commands.add_parser("items")
    listing.add_argument("--project")
    listing.add_argument("--status", choices=tuple(dict.fromkeys(store.STATUSES + store.PROJECT_STATUSES)))
    for command in ("get", "activity"):
        commands.add_parser(command).add_argument("ticket")
    create = commands.add_parser("create")
    create.add_argument(
        "--file", type=Path, required=True, help="UTF-8 JSON object containing editable fields"
    )
    update = commands.add_parser("update")
    update.add_argument("ticket")
    update.add_argument("--revision", type=int, required=True)
    update.add_argument("--file", type=Path, required=True)
    link = commands.add_parser("link")
    link.add_argument("source")
    link.add_argument("target")
    link.add_argument("kind", choices=("blocks", "relates to"))
    export = commands.add_parser("export")
    export.add_argument("--project")
    export.add_argument("--out", type=Path, required=True)
    importing = commands.add_parser("import")
    importing.add_argument("--file", type=Path, required=True)
    importing.add_argument("--new-key")
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            result = {
                "schema": store.Item.model_json_schema(),
                "read_only": ["id", "number", "created_at", "updated_at", "revision", "effective_tags"],
                "tag_semantics": "tags stores local overrides; tag_defaults is project-only; effective_tags is computed. Replace the whole map when updating. Remove a local key to resume inheritance; null is an explicit value.",
                "immutable_on_update": ["project_key"],
                "project_statuses": store.PROJECT_STATUSES,
                "work_statuses": store.STATUSES,
                "api_version": 3,
            }
        else:
            store.initialize(args.db)
            items, _ = store.load(args.db)

            def resolve(key):
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("Item references must be a ticket label or UUID string.")
                found = next((x for x in items if store.ticket(x) == key.upper() or x["id"] == key), None)
                if not found:
                    raise ValueError(f"Item not found: {key}")
                return found

            def payload():
                value = json.loads(args.file.read_text(encoding="utf-8-sig"))
                if not isinstance(value, dict):
                    raise ValueError("Provide a JSON object of editable fields.")
                if value.get("parent_id"):
                    value["parent_id"] = resolve(value["parent_id"])["id"]
                return value

            if args.command == "projects":
                result = [x for x in items if x["kind"] == "Project"]
            elif args.command == "items":
                result = [
                    x
                    for x in items
                    if (not args.project or x["project_key"] == args.project.upper())
                    and (not args.status or x["status"] == args.status)
                ]
            elif args.command == "get":
                result = resolve(args.ticket)
            elif args.command == "activity":
                result = store.activity(args.db, resolve(args.ticket)["id"])
            elif args.command == "create":
                result = store.save(args.db, payload(), actor=args.actor)
            elif args.command == "update":
                item = resolve(args.ticket)
                fields = payload()
                if "project_key" in fields and fields["project_key"] != item["project_key"]:
                    raise ValueError("Project keys cannot change on update.")
                result = store.save(args.db, fields, item["id"], args.revision, actor=args.actor)
            elif args.command == "link":
                store.add_link(args.db, resolve(args.source)["id"], resolve(args.target)["id"], args.kind)
                result = {"linked": True}
            elif args.command == "export":
                if args.project and not any(x["project_key"] == args.project.upper() for x in items):
                    raise ValueError("Project not found.")
                # Exclusive creation avoids silently overwriting an existing export.
                with args.out.open("x", encoding="utf-8") as output:
                    output.write(
                        store.export_snapshot(args.db, args.project.upper() if args.project else None)
                    )
                result = {"exported": str(args.out)}
            else:
                result = {"imported": store.import_snapshot(args.db, args.file.read_bytes(), args.new_key)}
        if args.command in ("projects", "items", "get", "create", "update"):
            current, _ = store.load(args.db)

            def present(item):
                return {**item, "effective_tags": store.effective_tags(item, current)}

            result = [present(x) for x in result] if isinstance(result, list) else present(result)
        print(json.dumps({"ok": True, "data": result}, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
