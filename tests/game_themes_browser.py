"""Exercise full style switching, density, dialogs and dragging on synthetic data."""

import re

from playwright.sync_api import expect

from organizer import store
from organizer.demo import seed
from organizer.game_themes import GAME_THEMES
from tests.browser_smoke import check_card_contrast, check_field_contrast
from tests.features_browser import ROOT, main


def check(page, db):
    seed(db)
    page.reload()
    for family, theme in GAME_THEMES.items():
        page.get_by_role("button", name="Preferences", exact=True).click()
        page.get_by_label("Theme palette", exact=True).click()
        page.get_by_role("option", name=theme["name"], exact=True).click()
        expect(page.locator(".palette-source")).to_contain_text(theme["name"])
        page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
        for mode in ("Light", "Dark"):
            page.get_by_role("button", name=mode, exact=True).click()
            expect(page.locator("body")).to_have_class(re.compile("body--" + mode.lower()))
            check_card_contrast(page)
            check_field_contrast(page)
            for compact in (False, True):
                switch = page.get_by_role("switch", name="Condensed view", exact=True)
                if switch.get_attribute("aria-checked") != str(compact).lower():
                    switch.click()
                expect(page.locator(".condensed-card")).to_have_count(12 if compact else 0)
                page.screenshot(
                    path=str(ROOT / "artifacts" / f"game-{family}-{mode}-{compact}.png"), full_page=True
                )
                title = page.locator(".ticket-title").first
                title.focus()
                title.press("Enter")
                expect(page.locator(".detail-card")).to_be_visible()
                page.get_by_role("button", name="Close details", exact=True).click()
            # Compact titles remain real mouse drag targets under each skin.
            card = page.locator(".board-column").first.locator(".ticket-card").first
            ticket = card.locator(".ticket-id").inner_text()
            card.locator(".ticket-title").drag_to(
                page.locator(".board-column").nth(1).locator(".ticket-list")
            )
            expect(page.locator(".board-column").nth(1).get_by_text(ticket, exact=True)).to_be_visible()
            item = next(x for x in store.load(db)[0] if store.ticket(x) == ticket)
            assert item["status"] == "Ready"
            store.save(db, {"status": "Backlog"}, item["id"], item["revision"])
            page.reload()
            assert store.setting(db, "palette") == family
        page.set_viewport_size({"width": 480, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), family
        page.set_viewport_size({"width": 1500, "height": 1080})
    # Replacing the stylesheet must restore ordinary palette shapes and fonts.
    page.get_by_role("button", name="Preferences", exact=True).click()
    page.get_by_label("Theme palette", exact=True).click()
    page.get_by_role("option", name="Sprig", exact=True).click()
    page.get_by_role("dialog").get_by_role("button", name="Done", exact=True).click()
    page.get_by_role("switch", name="Condensed view", exact=True).click()
    expect(page.locator(".condensed-card")).to_have_count(0)
    assert page.locator(".ticket-card").first.evaluate("e => getComputedStyle(e).borderRadius") == "10px"
    assert page.locator(".hero").count() == 0
    assert "Segoe UI" in page.locator("body").evaluate("e => getComputedStyle(e).fontFamily")


if __name__ == "__main__":
    main(check)
