from playwright.sync_api import expect

from organizer import store
from tests.browser_harness import ROOT, main
from tests.test_store import child


def check(page, db):
    root = store.save(db, {"kind": "Project", "project_key": "COLOR", "title": "Color project"})
    child(db, root)
    page.reload()
    page.locator(".project-card").get_by_role("button", name="Color project", exact=True).click()
    expect(page.locator(".project-overview")).to_be_visible()
    page.get_by_role("button", name="Edit project", exact=True).click()
    page.get_by_label("Project color", exact=True).click()
    expect(page.get_by_role("option")).to_have_count(12)
    page.screenshot(path=str(ROOT / "artifacts/project-color-options.png"), full_page=True)
    page.get_by_role("option", name="Cyan", exact=True).click()
    page.get_by_role("button", name="Save project", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    page.wait_for_function(
        "getComputedStyle(document.querySelector('.ticket-card')).borderTopColor === 'rgb(57, 175, 199)'"
    )
    page.reload()
    assert next(x for x in store.load(db)[0] if x["kind"] == "Project")["color"] == "Cyan"
    page.wait_for_function(
        "getComputedStyle(document.querySelector('.ticket-card')).borderTopColor === 'rgb(57, 175, 199)'"
    )


if __name__ == "__main__":
    main(check)
