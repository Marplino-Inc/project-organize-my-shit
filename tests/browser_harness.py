"""Shared browser runner using a disposable work-edition workspace."""

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main(checker):
    (ROOT / "artifacts").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sprig-work-test-") as directory:
        db = Path(directory) / "workspace.db"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        with (ROOT / "artifacts/work-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [sys.executable, "main.py", "--db", str(db), "--no-browser", "--port", str(port)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
            )
            try:
                for _ in range(100):
                    try:
                        with urlopen(url, timeout=1):
                            break
                    except OSError:
                        time.sleep(0.1)
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page(viewport={"width": 1500, "height": 1080}, reduced_motion="reduce")
                    errors = []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(url)
                    checker(page, db)
                    assert not errors, errors
                    browser.close()
                print("Work browser workflow passed")
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
