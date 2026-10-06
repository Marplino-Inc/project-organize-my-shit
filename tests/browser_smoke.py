"""Run directly with uv run python -m tests.browser_smoke (requires Chromium).

Uses a temporary workspace. Captures screenshots in ignored artifacts/.
"""

import json
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

from organizer import store
from organizer.demo import seed

ROOT = Path(__file__).resolve().parents[1]


def check_card_contrast(page):
    colors = page.locator(".ticket-title").first.evaluate("""element => ({
        foreground: getComputedStyle(element).color,
        background: getComputedStyle(element.closest('.ticket-card')).backgroundColor
    })""")

    def luminance(rgb):
        channels = [int(x) / 255 for x in re.findall(r"\d+", rgb)[:3]]
        linear = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in channels]
        return sum(x * weight for x, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    values = sorted(luminance(value) for value in colors.values())
    ratio = (values[1] + 0.05) / (values[0] + 0.05)
    assert ratio >= 4.5, f"Card title contrast too low: {ratio:.2f}:1"


def main():
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="organize-browser-") as directory:
        db = Path(directory) / "workspace.db"
        store.initialize(db)
        seed(db)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        with (artifacts / "browser-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [sys.executable, "main.py", "--db", str(db), "--no-browser", "--port", str(port)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
            )
            try:
                for _ in range(100):
                    try:
                        with urlopen(url, timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("App did not start")
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1080}, reduced_motion="reduce"
                    )
                    page = context.new_page()
                    errors, external_requests = [], []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on(
                        "request",
                        lambda request: (
                            external_requests.append(request.url) if not request.url.startswith(url) else None
                        ),
                    )
                    page.goto(url)
                    expect(page.get_by_role("button", name="New item", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Light", exact=True).click()
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--light\b"))
                    check_card_contrast(page)
                    page.screenshot(path=str(artifacts / "board-light.png"), full_page=True)
                    page.get_by_role("button", name="Dark", exact=True).click()
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--dark\b"))
                    page.reload()
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--dark\b"))
                    check_card_contrast(page)
                    page.screenshot(path=str(artifacts / "board-dark.png"), full_page=True)
                    page.get_by_role("button", name="System", exact=True).click()
                    page.emulate_media(color_scheme="light")
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--light\b"))
                    page.emulate_media(color_scheme="dark")
                    expect(page.locator("body")).to_have_class(re.compile(r"\bbody--dark\b"))
                    page.get_by_role("button", name="Light", exact=True).click()

                    # Create a project with a repository and an independent lifecycle.
                    page.get_by_role("button", name="New project", exact=True).last.click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Title", exact=True).fill("Browser-tested project")
                    dialog.get_by_label("Project key", exact=True).fill("WEB")
                    dialog.get_by_label("Repository URL (optional)", exact=True).fill(
                        "https://github.com/example/browser"
                    )
                    dialog.get_by_label("Status", exact=True).click()
                    page.get_by_role("option", name="Just Designing", exact=True).click()
                    dialog.get_by_role("button", name="Save project", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    expect(page.get_by_text("Just Designing", exact=True)).to_be_visible()
                    page.locator(".project-card").get_by_role(
                        "button", name="Browser-tested project", exact=True
                    ).click()
                    expect(page.get_by_role("link", name="Open repository")).to_have_attribute(
                        "href", "https://github.com/example/browser"
                    )

                    # Create a task and edit its content.
                    page.get_by_role("button", name="New item", exact=True).click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Title", exact=True).fill("Build a colorful card")
                    dialog.get_by_label("Description", exact=True).fill("Detailed notes\nSecond line")
                    dialog.get_by_label("Tags", exact=True).fill("Design, browser")
                    dialog.get_by_role("button", name="Save item", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    card = page.locator(".ticket-card").filter(has_text="Build a colorful card")
                    expect(card).to_be_visible()
                    card.get_by_role("button", name="Build a colorful card", exact=True).click()
                    expect(page.get_by_text("Detailed notes\nSecond line", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Edit item", exact=True).click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Title", exact=True).fill("A card worth keeping")
                    dialog.get_by_role("button", name="Save item", exact=True).click()
                    card = page.locator(".ticket-card").filter(has_text="A card worth keeping")
                    expect(card).to_be_visible()

                    # Both pointer and keyboard/menu pathways move persisted status.
                    card.locator(".drag-handle").drag_to(page.locator('[data-status="In progress"]'))
                    expect(page.locator('[data-status="In progress"] .ticket-card')).to_have_count(1)
                    expect(page.get_by_text("WEB-0002 → In progress", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Actions for WEB-0002", exact=True).click()
                    page.get_by_text("Move to Done", exact=True).click()
                    expect(page.locator('[data-status="Done"] .ticket-card')).to_have_count(1)
                    expect(page.get_by_text("Just Designing", exact=True)).to_be_visible()

                    # External updates become visible, and old dialogs cannot clobber them.
                    page.get_by_role("button", name="A card worth keeping", exact=True).click()
                    page.get_by_role("button", name="Edit item", exact=True).click()
                    task = next(x for x in store.load(db)[0] if store.ticket(x) == "WEB-0002")
                    store.save(
                        db,
                        {"title": "Updated by an agent"},
                        task["id"],
                        task["revision"],
                        actor="Browser test agent",
                    )
                    page.get_by_role("dialog").get_by_role("button", name="Save item", exact=True).click()
                    expect(
                        page.get_by_text("This item changed in another window.", exact=False)
                    ).to_be_visible()
                    page.get_by_role("dialog").get_by_role("button", name="Cancel", exact=True).click()
                    expect(page.get_by_role("button", name="Updated by an agent", exact=True)).to_be_visible(
                        timeout=7000
                    )

                    # Search, map, outline, dashboard, and exports.
                    page.get_by_role("button", name="My workspace", exact=True).click()
                    page.get_by_label("Search work", exact=True).fill("tooltip")
                    expect(page.locator(".ticket-card")).to_have_count(1)
                    page.get_by_role("button", name="Clear", exact=True).click()
                    expect(page.locator(".ticket-card")).to_have_count(13)
                    page.get_by_role("button", name="Map", exact=True).click()
                    expect(page.locator(".graph-shell svg")).to_be_visible()
                    page.locator(".graph-shell svg text").filter(has_text="ORG-0001").click()
                    expect(
                        page.get_by_role("dialog").get_by_text("A calmer project workspace", exact=True)
                    ).to_be_visible()
                    page.get_by_role("button", name="Close details", exact=True).click()
                    page.locator(".q-notification").evaluate_all(
                        "nodes => nodes.forEach(node => node.style.visibility = 'hidden')"
                    )
                    page.screenshot(path=str(artifacts / "map-light.png"), full_page=True)
                    page.get_by_role("button", name="Outline", exact=True).click()
                    expect(page.locator(".outline-row")).to_have_count(17)
                    page.get_by_role("button", name="Dashboard", exact=True).click()
                    expect(page.get_by_text("Work by status", exact=True)).to_be_visible()
                    page.screenshot(path=str(artifacts / "dashboard-light.png"), full_page=True)
                    page.get_by_role("button", name="Share", exact=True).click()
                    with page.expect_download() as download:
                        page.get_by_role("button", name="Export project snapshot", exact=True).click()
                    output = Path(directory) / "snapshot.json"
                    download.value.save_as(output)
                    assert len(store.parse_snapshot(output.read_bytes()).items) == 17
                    with page.expect_download() as download:
                        page.get_by_role("button", name="Download read-only report", exact=True).click()
                    report = Path(directory) / "report.html"
                    download.value.save_as(report)
                    assert "Browser-tested project" in report.read_text(encoding="utf-8")
                    page.get_by_role("button", name="Close", exact=True).click()
                    page.get_by_label("Project stage", exact=True).click()
                    page.get_by_role("option", name="Just Designing", exact=True).click()
                    expect(page.locator(".project-card")).to_have_count(1)
                    page.get_by_role("button", name="My workspace", exact=True).click()
                    expect(page.locator(".project-card")).to_have_count(4)
                    # UI snapshot import previews, then adds a separate project copy.
                    single = Path(directory) / "single.json"
                    single.write_text(store.export_snapshot(db, "WEB"), encoding="utf-8")
                    page.get_by_role("button", name="Share", exact=True).click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("New key (optional, single-project imports)", exact=True).fill("COPY")
                    dialog.locator('input[type="file"]').set_input_files(single)
                    expect(
                        dialog.get_by_text("Ready: 1 project(s), 2 items, 0 relationships.", exact=True)
                    ).to_be_visible()
                    dialog.get_by_role("button", name="Import snapshot", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    expect(page.locator(".project-card")).to_have_count(5)
                    page.get_by_role("button", name="Preferences", exact=True).click()
                    page.get_by_role("dialog").get_by_role("button", name="1–5", exact=True).click()
                    page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
                    assert store.setting(db, "effort_scale") == "1–5"
                    page.get_by_role("button", name="Board", exact=True).click()
                    expect(page.locator(".ticket-card")).to_have_count(14)
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.screenshot(path=str(artifacts / "board-mobile.png"), full_page=True)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                        "Page overflows horizontally"
                    )
                    assert not errors, errors
                    assert not external_requests, external_requests
                    browser.close()
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "checks": "themes, project lifecycle, repository, CRUD, drag/menu status, optimistic edits, agent refresh, filters, views, exports, responsive layout, offline assets",
                            "screenshots": str(artifacts),
                        }
                    )
                )
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
