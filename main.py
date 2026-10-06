import argparse
from pathlib import Path

from nicegui import ui

from organizer.config import database_path
from organizer.demo import seed
from organizer.store import initialize
from organizer.views import register


def main():
    parser = argparse.ArgumentParser(description="Organize — a local project workspace")
    parser.add_argument("--demo", action="store_true", help="Use a separate sample workspace")
    parser.add_argument("--db", type=Path, help="Use a particular SQLite workspace")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.demo and args.db:
        parser.error("Use either --demo or --db, so sample data never enters a personal database.")
    path = args.db or database_path(args.demo)
    initialize(path)
    if args.demo:
        seed(path)
    register(path, args.demo)
    ui.run(
        host="127.0.0.1",
        port=args.port,
        title="Organize · Your project workspace",
        favicon="🗂️",
        reload=False,
        show=not args.no_browser,
        dark=None,
    )


if __name__ == "__main__":
    main()
