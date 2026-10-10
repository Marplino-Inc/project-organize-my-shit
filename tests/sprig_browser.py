"""Final visual/drag workflow: uv run python -m tests.sprig_browser."""

from playwright.sync_api import expect

from organizer import store
from tests.features_browser import ROOT, check, main


def sprig_check(page, db):
    check(page, db)
    expect(page).to_have_title("Sprig · Your project workspace")
    expect(page.locator(".brand-name")).to_have_text("Sprig")
    expect(page.locator(".brand-logo svg")).to_have_count(1)
    items, _ = store.load(db)
    root = next(x for x in items if store.ticket(x) == "WOW-0001")
    definitions = {**root["feature_definitions"], "new-ui": {"name": "Interface", "description": ""}}
    store.save(db, {"feature_definitions": definitions}, root["id"], root["revision"])
    for task in [x for x in items if x["project_key"] == "WOW" and x["kind"] == "Task"]:
        store.save(
            db,
            {"feature_ids": list(definitions) if task["title"] == "Add themes" else []},
            task["id"],
            task["revision"],
        )
    page.get_by_role("button", name="Clear", exact=True).last.click()
    colored = page.locator(".ticket-card").filter(has_text="Add themes")
    plain = page.locator(".ticket-card").filter(has_text="Readable labels")
    expect(colored.locator(".feature-band-segment")).to_have_count(2, timeout=10000)
    expect(plain.locator(".feature-band")).to_have_count(0)
    colors = colored.locator(".feature-band-segment").evaluate_all(
        "nodes => nodes.map(n => getComputedStyle(n).backgroundColor)"
    )
    toggle = page.get_by_role("switch", name="Color by Feature", exact=True)
    expect(toggle).to_have_attribute("aria-checked", "true")
    toggle.click()
    expect(colored.locator(".feature-band")).to_have_count(0)
    page.reload()
    expect(toggle).to_have_attribute("aria-checked", "false")
    toggle.click()
    expect(colored.locator(".feature-band-segment")).to_have_count(2)
    page.get_by_role("button", name="Preferences", exact=True).click()
    slider = page.get_by_role("slider", name="Card color band thickness", exact=True)
    expect(slider).to_have_attribute("aria-valuenow", "5")
    slider.locator("[tabindex]").press("ArrowRight")
    expect(slider).to_have_attribute("aria-valuenow", "6")
    page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    page.reload()
    assert store.setting(db, "card_band_width") == "6"
    expect(colored.locator(".feature-band")).to_have_css("width", "6px")
    for condensed in (False, True):
        density = page.get_by_role("switch", name="Condensed view", exact=True)
        if density.get_attribute("aria-checked") != str(condensed).lower():
            density.click()
        expect(density).to_have_attribute("aria-checked", str(condensed).lower())
        expect(page.locator(".condensed-board")).to_have_count(1 if condensed else 0)
        expect(colored).to_have_css("border-left-width" if condensed else "border-top-width", "6px")
        heights = colored.locator(".feature-band-segment").evaluate_all(
            "nodes => nodes.map(n => n.getBoundingClientRect().height)"
        )
        assert abs(heights[0] - heights[1]) < 1
        # Drag from card padding, then from its title, into empty lanes.
        for status, title_drag in (("Ready", False), ("In progress", True), ("Done", False)):
            target = page.locator(f'[data-status="{status}"]')
            if title_drag:
                colored.locator(".ticket-title").drag_to(target)
            else:
                colored.drag_to(target, source_position={"x": 100, "y": 3})
            expect(target.locator(".ticket-card").filter(has_text="Add themes")).to_have_count(1)
            expect(page.get_by_role("dialog")).to_have_count(0)
            saved = next(x for x in store.load(db)[0] if x["title"] == "Add themes")
            assert saved["status"] == status
            assert len(saved["feature_ids"]) == 2
        colored.click(position={"x": 100, "y": 3})
        expect(page.get_by_role("dialog")).to_be_visible()
        page.get_by_role("button", name="Close details", exact=True).click()
        for mode in ("Light", "Dark"):
            page.get_by_role("button", name=mode, exact=True).click()
            page.wait_for_function(
                "mode => document.body.classList.contains('body--' + mode)", arg=mode.lower()
            )
            page.screenshot(path=str(ROOT / f"artifacts/sprig-{mode}-{condensed}.png"), full_page=True)
        # Return to Backlog through the shared store to exercise the same path in both densities.
        saved = next(x for x in store.load(db)[0] if x["title"] == "Add themes")
        store.save(db, {"status": "Backlog"}, saved["id"], saved["revision"])
        expect(page.locator('[data-status="Backlog"] .ticket-card')).to_have_count(2, timeout=10000)
    assert (
        colored.locator(".feature-band-segment").evaluate_all(
            "nodes => nodes.map(n => getComputedStyle(n).backgroundColor)"
        )
        == colors
    )


if __name__ == "__main__":
    main(sprig_check)
