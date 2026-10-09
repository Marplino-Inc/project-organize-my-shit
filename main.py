import argparse
import hashlib
import json
import socket
import tomllib
import webbrowser
from pathlib import Path
from urllib.request import urlopen

from nicegui import app, ui

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
    url = f"http://127.0.0.1:{args.port}"
    version = tomllib.loads(Path(__file__).with_name("pyproject.toml").read_text())["project"]["version"]
    identity = {
        "app": "organize",
        "workspace": hashlib.sha256(str(path.resolve()).casefold().encode()).hexdigest(),
        "version": version,
    }
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError:
            try:
                with urlopen(url + "/_organize/instance", timeout=2) as response:
                    running = json.load(response)
            except (OSError, ValueError):
                running = None
            if running == identity:
                print(f"Organize is already running at {url}. Reusing your workspace.")
                if not args.no_browser:
                    webbrowser.open(url)
                return
            parser.exit(
                1,
                f"Port {args.port} is already in use. Open {url} to check the existing app. Close the older app before upgrading, or choose another -Port for a different workspace. No database changes were made.\n",
            )

    @app.get("/_organize/instance")
    def instance():
        return identity

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
