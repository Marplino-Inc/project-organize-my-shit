from urllib.parse import urlparse

from playwright.sync_api import expect

from organizer import store, themes
from tests.browser_harness import main
from tests.test_store import child


def check(page, db):
    root = store.save(db, {"kind": "Project", "project_key": "WORK", "title": "Work project"})
    child(
        db,
        root,
        description='## Notes\n\n- A task\n\n<img src="https://example.invalid/tracker" onerror="window.bad=true">',
    )
    page.reload()
    expect(page.get_by_label("Feature", exact=True)).to_have_count(0)
    expect(page.get_by_role("switch", name="Color by Feature", exact=True)).to_have_count(0)
    page.get_by_label("Sort by", exact=True).click()
    expect(page.get_by_role("option")).to_have_count(3)
    page.keyboard.press("Escape")
    remote = []
    page.on(
        "request",
        lambda request: (
            remote.append(request.url) if urlparse(request.url).hostname not in ("127.0.0.1", None) else None
        ),
    )
    # Exercise local assets for every retained palette, both modes.
    for family in themes.FAMILIES.values():
        page.get_by_role("button", name="Preferences", exact=True).click()
        page.get_by_label("Theme palette", exact=True).click()
        page.get_by_role("option", name=family["name"], exact=True).click()
        page.keyboard.press("Escape")
        for mode in ("Dark", "Light"):
            page.get_by_role("button", name=mode, exact=True).click()
            expect(page.locator(".ticket-card")).to_be_visible()
    violations = []
    page.on(
        "console",
        lambda message: (
            violations.append(message.text) if "Content Security Policy" in message.text else None
        ),
    )
    page.locator(".ticket-card").click()
    expect(page.locator(".work-description h2")).to_have_text("Notes")
    expect(page.locator(".work-description [onerror]")).to_have_count(0)
    assert not page.evaluate("Boolean(window.bad)")
    assert violations, "Remote image should be blocked by CSP"
    # A blocked request may be reported by Playwright, but must not reach the network.
    page.get_by_role("button", name="Close details", exact=True).click()
    response = page.request.get(page.url, headers={"Origin": "https://evil.example"})
    assert response.status == 403
    response = page.request.get(page.url, headers={"Host": "evil.example"})
    assert response.status == 403
    page.get_by_role("button", name="Open WORK project details", exact=True).click()
    page.get_by_role("button", name="Edit item", exact=True).click()
    expect(page.get_by_text("Features", exact=True)).to_have_count(0)
    page.get_by_role("button", name="Cancel", exact=True).click()
    assert all(url.startswith("https://example.invalid/tracker") for url in remote), remote


if __name__ == "__main__":
    main(check)
