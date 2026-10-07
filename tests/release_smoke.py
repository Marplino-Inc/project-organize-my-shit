"""Validate the actual release ZIP on Windows, with data in a temporary workspace."""

import argparse
import json
import os
import re
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("The Windows launcher check requires Windows.")
    with tempfile.TemporaryDirectory(prefix="organize release ") as directory:
        root = Path(directory)
        with ZipFile(args.archive) as archive:
            names = archive.namelist()
            assert not any(
                part in {".git", ".venv", "artifacts", "__pycache__"}
                for name in names
                for part in Path(name).parts
            )
            assert not any(name.endswith((".db", ".sqlite", ".env")) for name in names)
            for name in names:
                if not (root / name).resolve().is_relative_to(root.resolve()):
                    raise ValueError("Archive contains a path outside its destination.")
            archive.extractall(root)
        app_root = next(root.glob("*/Start.cmd")).parent
        db = root / "workspace data" / "release-test.db"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        log_path = root / "launcher.log"
        with log_path.open("w", encoding="utf-8") as log:

            def start():
                process = subprocess.Popen(
                    [
                        os.environ["COMSPEC"],
                        "/d",
                        "/c",
                        "Start.cmd",
                        "-Database",
                        str(db),
                        "-Port",
                        str(port),
                        "-NoBrowser",
                    ],
                    cwd=app_root,
                    stdout=log,
                    stderr=log,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                for _ in range(300):
                    if process.poll() is not None:
                        raise RuntimeError(
                            "Launcher stopped: " + log_path.read_text(encoding="utf-8", errors="replace")
                        )
                    try:
                        with urlopen(url, timeout=0.5) as response:
                            if response.status == 200:
                                return process
                    except OSError:
                        time.sleep(0.1)
                stop(process)
                raise RuntimeError(
                    "Launcher did not become ready: " + log_path.read_text(encoding="utf-8", errors="replace")
                )

            def stop(process):
                # Only the process tree created by this test is terminated.
                if process.poll() is None:
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=True
                    )
                    process.wait(timeout=10)

            process = start()
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(url)
                    page.get_by_role("button", name="Create your first project", exact=True).click()
                    page.get_by_label("Title", exact=True).fill("Release persistence check")
                    page.get_by_label("Project key", exact=True).fill("REL")
                    page.get_by_role("button", name="Save project", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    expect(page.locator(".project-card")).to_have_count(1)
                    expect(
                        page.locator(".project-card").get_by_text("Still a Dream", exact=True)
                    ).to_be_visible()
                    page.get_by_role("button", name="Dark", exact=True).click()
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--dark\b"))
                    page.get_by_label("Palette", exact=True).click()
                    page.get_by_role("option", name="Shiny Mint", exact=True).click()
                    page.wait_for_function(
                        "getComputedStyle(document.body).getPropertyValue('--canvas').trim() === '#19231f'"
                    )
                    # Verify the preference write completed before terminating the process.
                    page.reload()
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--dark\b"))
                    page.close()
                    stop(process)
                    process = start()
                    page = browser.new_page()
                    page.goto(url)
                    expect(page.get_by_label("Palette", exact=True)).to_have_value("Shiny Mint")
                    expect(
                        page.locator(".project-card").get_by_role(
                            "button", name="Release persistence check", exact=True
                        )
                    ).to_be_visible()
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--dark\b"))
                    assert db.exists()
                    assert not list(app_root.rglob("*.db")), (
                        "Working data leaked into the application directory"
                    )
                    browser.close()
            finally:
                stop(process)
    print(
        json.dumps(
            {
                "ok": True,
                "archive": str(args.archive),
                "checks": "clean archive, Start.cmd from a path with spaces, first project, full process restart, theme/data persistence",
            }
        )
    )


if __name__ == "__main__":
    main()
