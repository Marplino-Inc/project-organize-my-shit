"""Feature workflow in a disposable workspace: uv run python -m tests.features_browser."""

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

from organizer import store

ROOT = Path(__file__).resolve().parents[1]


def check(page, db):
    page.get_by_role("button", name="Create your first project", exact=True).click()
    dialog = page.get_by_role("dialog")
    dialog.get_by_label("Title", exact=True).fill("WoW addon")
    dialog.get_by_label("Project key", exact=True).fill("WOW")
    dialog.get_by_text("Features", exact=True).click()
    for i, name in enumerate(("UI development", "Accessibility")):
        dialog.get_by_role("button", name="Add feature", exact=True).click()
        dialog.get_by_label("Feature name", exact=True).nth(i).fill(name)
        dialog.get_by_label("Feature description (optional)", exact=True).nth(i).fill("Readable themes")
    dialog.get_by_role("button", name="Save project", exact=True).click()
    expect(dialog).to_have_count(0)
    page.locator(".project-card").get_by_role("button", name="WoW addon", exact=True).click()
    page.get_by_role("button", name="New item", exact=True).click()
    dialog.get_by_label("Title", exact=True).fill("Add themes")
    dialog.get_by_label("Features", exact=True).click()
    page.get_by_role("option", name="UI development", exact=True).click()
    page.get_by_role("option", name="Accessibility", exact=True).click()
    page.keyboard.press("Escape")
    dialog.get_by_role("button", name="Save item", exact=True).click()
    expect(dialog).to_have_count(0)
    expect(page.locator(".ticket-card .feature-badge")).to_have_count(2)
    for name in ("UI development", "Accessibility"):
        page.get_by_label("Feature", exact=True).click()
        page.get_by_role("option", name=name, exact=True).click()
        expect(page.locator(".ticket-card")).to_have_count(1)
        expect(page.locator(".ticket-id")).to_have_text("WOW-0002")
    page.get_by_role("button", name="New item", exact=True).click()
    dialog.get_by_label("Title", exact=True).fill("Readable labels")
    expect(dialog.locator(".q-chip")).to_contain_text(["Accessibility"])
    dialog.get_by_role("button", name="Save item", exact=True).click()
    expect(dialog).to_have_count(0)
    expect(page.locator(".ticket-card")).to_have_count(2)
    page.get_by_role("button", name="Edit project", exact=True).click()
    dialog.get_by_text("Features", exact=True).click()
    expect(dialog.get_by_role("button", name="Remove feature", exact=True).first).to_be_disabled()
    dialog.get_by_label("Feature name", exact=True).nth(1).fill("Inclusive design")
    dialog.get_by_role("button", name="Save project", exact=True).click()
    expect(dialog).to_have_count(0)
    expect(page.get_by_label("Feature", exact=True)).to_have_value("Inclusive design")
    expect(page.locator(".ticket-card")).to_have_count(2)
    page.screenshot(path=str(ROOT / "artifacts/features-board-light.png"), full_page=True)
    page.get_by_role("button", name="Dark", exact=True).click()
    page.get_by_role("switch", name="Condensed view", exact=True).click()
    expect(page.locator(".condensed-card")).to_have_count(2)
    expect(page.locator(".ticket-card .feature-badge")).to_have_count(0)
    page.get_by_role("button", name="Add themes", exact=True).click()
    expect(dialog.locator(".feature-badge")).to_have_count(2)
    page.screenshot(path=str(ROOT / "artifacts/features-detail-dark.png"), full_page=True)
    dialog.get_by_role("button", name="Close details", exact=True).click()
    items, _ = store.load(db)
    task = next(x for x in items if store.ticket(x) == "WOW-0002")
    store.save(db, {"feature_ids": []}, task["id"], task["revision"], actor="Feature browser test")
    expect(page.locator(".ticket-card")).to_have_count(1, timeout=10000)
    page.get_by_role("button", name="Clear", exact=True).last.click()
    expect(page.locator(".ticket-card")).to_have_count(2)
    page.reload()
    page.locator(".project-card").get_by_role("button", name="WoW addon", exact=True).click()
    page.get_by_label("Feature", exact=True).click()
    page.get_by_role("option", name="UI development", exact=True).click()
    expect(page.locator(".ticket-card")).to_have_count(0)
    # Removing the now-unused selected feature clears the filter rather than breaking the page.
    page.get_by_role("button", name="Edit project", exact=True).click()
    dialog.get_by_text("Features", exact=True).click()
    dialog.get_by_role("button", name="Remove feature", exact=True).first.click()
    dialog.get_by_role("button", name="Save project", exact=True).click()
    expect(dialog).to_have_count(0)
    expect(page.locator(".ticket-card")).to_have_count(2)
    assert store.progress(store.load(db)[0]) == (0, 2)
    page.get_by_role("button", name="New project", exact=True).last.click()
    dialog.get_by_label("Title", exact=True).fill("Another project")
    dialog.get_by_label("Project key", exact=True).fill("AAA")
    dialog.get_by_role("button", name="Save project", exact=True).click()
    expect(dialog).to_have_count(0)
    page.get_by_role("button", name="Home", exact=True).click()
    page.get_by_label("Feature", exact=True).click()
    page.get_by_role("option", name="WOW · Inclusive design", exact=True).click()
    page.get_by_role("button", name="New item", exact=True).click()
    expect(dialog.get_by_label("Project", exact=True)).to_have_value("WOW · WoW addon")
    expect(dialog.locator(".q-chip")).to_contain_text(["Inclusive design"])
    dialog.get_by_role("button", name="Cancel", exact=True).click()


def main():
    (ROOT / "artifacts").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="organize-features-") as directory:
        db = Path(directory) / "workspace.db"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        with (ROOT / "artifacts/features-server.log").open("w", encoding="utf-8") as log:
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
                    check(page, db)
                    assert not errors, errors
                    browser.close()
                print("Feature browser workflow passed")
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
