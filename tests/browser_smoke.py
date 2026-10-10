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

from organizer import store, themes
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
                    for family, theme in themes.FAMILIES.items():
                        page.get_by_role("button", name="Preferences", exact=True).click()
                        picker = page.get_by_label("Theme palette", exact=True)
                        picker_id = picker.get_attribute("id")
                        expect(picker).to_have_attribute("readonly", "")
                        picker.click()
                        page.get_by_role("option", name=theme["name"], exact=True).click()
                        expect(page.locator(".palette-source")).to_contain_text(theme["source"])
                        assert picker.get_attribute("id") == picker_id
                        assert (
                            page.locator(".palette-source").bounding_box()["y"]
                            < page.locator(".palette-preview").bounding_box()["y"]
                        )
                        if theme["url"]:
                            expect(page.locator(".palette-source a")).to_have_attribute("href", theme["url"])
                        page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
                        page.wait_for_function(
                            "color => getComputedStyle(document.body).getPropertyValue('--canvas').trim() === color",
                            arg=theme["dark"][0]
                            if "body--dark" in page.locator("body").get_attribute("class")
                            else theme["light"][0],
                        )
                        for mode in ("Light", "Dark"):
                            page.get_by_role("button", name=mode, exact=True).click()
                            expect(page.locator("body")).to_have_class(
                                re.compile(r"\bbody--" + mode.lower() + r"\b")
                            )
                            check_card_contrast(page)
                            page.screenshot(
                                path=str(artifacts / f"theme-{family}-{mode.lower()}.png"), full_page=True
                            )
                        page.reload()
                        assert store.setting(db, "palette", "organize") == family
                    page.get_by_role("button", name="Light", exact=True).click()
                    expect(page.get_by_label("Palette", exact=True)).to_have_count(0)
                    expect(page.get_by_role("button", name="System", exact=True)).to_have_count(0)
                    page.get_by_role("button", name="Preferences", exact=True).click()
                    page.get_by_label("Theme palette", exact=True).click()
                    page.get_by_role("option", name="Material Blue", exact=True).click()
                    expect(page.locator(".palette-source")).to_contain_text("Google Material 3")
                    expect(page.locator(".palette-sample")).to_contain_text(
                        "A clearer view of your next step"
                    )
                    page.screenshot(path=str(artifacts / "preferences-source.png"), full_page=True)
                    page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()

                    # Create a project with a repository and an independent lifecycle.
                    page.get_by_role("button", name="New project", exact=True).last.click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Title", exact=True).fill("Browser-tested project")
                    dialog.get_by_label("Project key", exact=True).fill("WEB")
                    dialog.get_by_label("Description", exact=True).fill(
                        "A focused overview of the browser project."
                    )
                    dialog.get_by_label("Repository URL (optional)", exact=True).fill(
                        "https://github.com/example/browser"
                    )
                    dialog.get_by_label("Status", exact=True).click()
                    page.get_by_role("option", name="Just Designing", exact=True).click()
                    dialog.get_by_role("button", name="Add default tag", exact=True).click()
                    dialog.get_by_label("Default tag name", exact=True).fill("owner")
                    dialog.get_by_label("Default tag value", exact=True).fill("Gary")
                    dialog.get_by_role("button", name="Add default tag", exact=True).click()
                    dialog.get_by_label("Default tag name", exact=True).nth(1).fill("release")
                    dialog.get_by_role("checkbox", name="Null", exact=True).nth(1).click()
                    dialog.get_by_role("button", name="Save project", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    expect(page.get_by_text("Just Designing", exact=True)).to_be_visible()
                    page.locator(".project-card").get_by_role(
                        "button", name="Browser-tested project", exact=True
                    ).click()
                    expect(page.get_by_role("link", name="Open repository")).to_have_attribute(
                        "href", "https://github.com/example/browser"
                    )
                    expect(page.locator(".project-heading")).to_have_text("Browser-tested project")
                    expect(page.locator(".project-description")).to_have_text(
                        "A focused overview of the browser project."
                    )
                    expect(page.get_by_text("Projects in scope", exact=True)).to_have_count(0)
                    expect(page.get_by_label("Project stage", exact=True)).to_have_count(0)

                    # Create a task and edit its content.
                    page.get_by_role("button", name="New item", exact=True).click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Title", exact=True).fill("Build a colorful card")
                    dialog.get_by_label("Description", exact=True).fill("Detailed notes\nSecond line")
                    expect(dialog.get_by_label("Tag value", exact=True).first).to_be_disabled()
                    dialog.get_by_role("switch", name="Override", exact=True).first.click()
                    dialog.get_by_role("checkbox", name="Null", exact=True).first.click()
                    expect(dialog.get_by_label("Tag value", exact=True).first).to_be_disabled()
                    dialog.get_by_role("button", name="Add tag", exact=True).click()
                    dialog.get_by_label("Tag name", exact=True).fill("area")
                    dialog.get_by_label("Tag value", exact=True).last.fill("Design")
                    dialog.get_by_role("button", name="Save item", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    card = page.locator(".ticket-card").filter(has_text="Build a colorful card")
                    expect(card).to_be_visible()
                    expect(card.get_by_text("owner: (null)", exact=True)).to_be_visible()
                    expect(card.get_by_text("release: (null)", exact=True)).to_be_visible()
                    expect(card.locator(".ticket-footer")).to_have_count(0)
                    card.click(position={"x": 5, "y": 35})
                    expect(page.locator(".detail-card")).to_be_visible()
                    bounds = page.locator(".detail-card").bounding_box()
                    assert abs(bounds["x"] + bounds["width"] / 2 - 720) < 5
                    assert abs(bounds["y"] + bounds["height"] / 2 - 540) < 5
                    expect(page.get_by_text("Detailed notes\nSecond line", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Edit item", exact=True).click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Title", exact=True).fill("A card worth keeping")
                    dialog.get_by_role("switch", name="Override", exact=True).first.click()
                    expect(dialog.get_by_label("Tag value", exact=True).first).to_have_value("Gary")
                    dialog.get_by_role("button", name="Save item", exact=True).click()
                    card = page.locator(".ticket-card").filter(has_text="A card worth keeping")
                    expect(card).to_be_visible()
                    expect(card.get_by_text("owner: Gary", exact=True)).to_be_visible()
                    root = next(x for x in store.load(db)[0] if store.ticket(x) == "WEB-0001")
                    store.save(
                        db,
                        {"tag_defaults": {"owner": "Agent", "release": None}},
                        root["id"],
                        root["revision"],
                    )
                    expect(card.get_by_text("owner: Agent", exact=True)).to_be_visible(timeout=7000)

                    # A project can reuse the entire set without an ongoing link to its source.
                    page.get_by_role("button", name="New project", exact=True).last.click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Copy defaults from project", exact=True).click()
                    page.get_by_role("option", name=re.compile("WEB.*Browser-tested project")).click()
                    dialog.get_by_role("button", name="Copy set", exact=True).click()
                    expect(dialog.get_by_label("Default tag name", exact=True).first).to_have_value("owner")
                    expect(dialog.get_by_label("Default tag value", exact=True).first).to_have_value("Agent")
                    expect(dialog.get_by_role("checkbox", name="Null", exact=True).nth(1)).to_be_checked()
                    expect(dialog.locator(".q-checkbox__inner--truthy")).to_have_css(
                        "color", "rgb(37, 94, 170)"
                    )
                    page.screenshot(path=str(artifacts / "project-tag-defaults.png"), full_page=True)
                    dialog.get_by_role("button", name="Cancel", exact=True).click()

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

                    # Core board search, tags, removed navigation, and exports.
                    page.get_by_role("button", name="My workspace", exact=True).click()
                    page.get_by_label("Search work", exact=True).fill("tooltip")
                    expect(page.locator(".ticket-card")).to_have_count(1)
                    page.get_by_role("button", name="Clear", exact=True).last.click()
                    expect(page.locator(".ticket-card")).to_have_count(13)
                    page.get_by_label("Tag", exact=True).click()
                    page.get_by_label("Tag", exact=True).fill("owner")
                    page.get_by_role("option", name="owner: Agent", exact=True).click()
                    expect(page.locator(".ticket-card")).to_have_count(1)
                    page.get_by_role("button", name="Clear", exact=True).last.click()
                    expect(page.locator(".ticket-card")).to_have_count(13)
                    for removed in ("Outline", "Map", "Dashboard"):
                        expect(page.get_by_role("button", name=removed, exact=True)).to_have_count(0)
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
                    expect(page.get_by_role("dialog").get_by_text("Effort labels", exact=True)).to_have_count(
                        0
                    )
                    page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
                    expect(page.locator(".ticket-card")).to_have_count(14)
                    full_height = page.locator(".ticket-card").first.bounding_box()["height"]
                    page.get_by_role("switch", name="Condensed view", exact=True).click()
                    expect(page.locator(".condensed-card")).to_have_count(14)
                    expect(
                        page.locator(
                            ".ticket-card .tags, .ticket-card .ticket-context, .ticket-card .ticket-footer"
                        )
                    ).to_have_count(0)
                    assert page.locator(".ticket-card").first.bounding_box()["height"] < full_height
                    page.reload()
                    expect(page.locator(".condensed-card")).to_have_count(14)
                    expect(page.get_by_role("switch", name="Condensed view", exact=True)).to_be_checked()
                    page.locator(".condensed-card .ticket-title").first.press("Enter")
                    expect(page.locator(".detail-card")).to_be_visible()
                    page.get_by_role("button", name="Close details", exact=True).click()
                    page.screenshot(path=str(artifacts / "board-condensed.png"), full_page=True)
                    # The main panel reaches the right edge even on an ultrawide display.
                    page.set_viewport_size({"width": 2560, "height": 1080})
                    panel = page.locator("main.main")
                    bounds = panel.bounding_box()
                    assert abs(bounds["x"] + bounds["width"] - 2560) < 2
                    expanded_width = bounds["width"]
                    page.locator(".project-card").filter(has_text="WEB-0001").get_by_role(
                        "button", name="Browser-tested project", exact=True
                    ).click()
                    expect(page.locator(".project-overview")).to_be_visible()
                    page.get_by_role("button", name="Toggle sidebar", exact=True).click()
                    expect(page.locator("aside.sidebar")).not_to_be_visible()
                    expect(page.get_by_role("button", name="Toggle sidebar", exact=True)).to_have_attribute(
                        "aria-expanded", "false"
                    )
                    assert panel.bounding_box()["width"] > expanded_width
                    assert abs(panel.bounding_box()["width"] - 2560) < 2
                    page.get_by_role("button", name="Home", exact=True).click()
                    expect(page.locator(".project-overview")).to_have_count(0)
                    expect(page.locator(".project-card")).to_have_count(5)
                    page.reload()
                    expect(page.locator("aside.sidebar")).not_to_be_visible()
                    page.get_by_role("button", name="Preferences", exact=True).click()
                    expect(page.locator(".palette-preview")).to_be_visible()
                    page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
                    expect(page.get_by_role("dialog")).to_have_count(0)
                    page.screenshot(path=str(artifacts / "board-wide-collapsed.png"), full_page=True)
                    page.get_by_role("button", name="Toggle sidebar", exact=True).press("Enter")
                    expect(page.locator("aside.sidebar")).to_be_visible()
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
                            "checks": "themes, project lifecycle, repository, CRUD, drag/menu status, optimistic edits, agent refresh, filters, board-only navigation, palette sources, sidebar collapse, Home, exports, ultrawide/mobile layout, offline assets",
                            "screenshots": str(artifacts),
                        }
                    )
                )
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
