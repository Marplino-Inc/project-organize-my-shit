from playwright.sync_api import expect

from organizer import history, store
from tests.browser_harness import ROOT, main
from tests.test_store import child


def check(page, db):
    root = store.save(db, {"kind": "Project", "project_key": "HIST", "title": "History project"})
    task = child(db, root, description="## Notes\n\n- First\n- Second\n\n" + "Long note.\n\n" * 30)
    page.reload()
    expect(page.get_by_text("Your ideas. Taking shape.", exact=True)).to_have_count(0)
    page.get_by_role("button", name="Undo and redo", exact=True).click()
    expect(page.get_by_text("Nothing to undo.", exact=True)).to_be_visible()
    expect(page.get_by_text("Nothing to redo.", exact=True)).to_be_visible()
    page.get_by_role("button", name="Close history", exact=True).click()
    page.locator(".ticket-card").click()
    body = page.locator(".work-description")
    expect(body.locator("h2")).to_have_text("Notes")
    expect(body.locator("li")).to_have_count(2)
    assert body.evaluate("el => el.clientHeight >= el.scrollHeight - 1")
    page.get_by_role("button", name="Edit item", exact=True).click()
    page.get_by_label("Title", exact=True).fill("Edited by UI")
    page.get_by_role("button", name="Save item", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    assert len(history.state(db)) == 1
    page.get_by_role("button", name="Undo and redo", exact=True).click()
    expect(page.locator(".history-column").nth(0)).to_contain_text("Redo")
    expect(page.locator(".history-column").nth(1)).to_contain_text("Current workspace")
    expect(page.locator(".history-column").nth(2)).to_contain_text("Undo")
    page.get_by_role("button", name="Undo", exact=True).click()
    expect(page.locator(".ticket-card")).to_contain_text("A task")
    page.get_by_role("button", name="Redo", exact=True).click()
    expect(page.locator(".ticket-card")).to_contain_text("Edited by UI")
    page.screenshot(path=str(ROOT / "artifacts/history-dialog.png"), full_page=True)
    page.get_by_role("button", name="Close history", exact=True).click()
    page.reload()
    page.get_by_role("button", name="Undo and redo", exact=True).click()
    expect(page.get_by_role("button", name="Undo", exact=True)).to_be_visible()
    current = next(x for x in store.load(db)[0] if x["id"] == task["id"])
    store.save(db, {"title": "Agent edit"}, task["id"], current["revision"], actor="Agent")
    page.get_by_role("button", name="Undo", exact=True).click()
    expect(
        page.get_by_text("This field changed outside UI history. No changes were applied.", exact=True)
    ).to_be_visible()
    page.get_by_role("button", name="Close history", exact=True).click()
    expect(page.locator(".ticket-card")).to_contain_text("Agent edit", timeout=10000)
    page.locator(".ticket-card .drag-handle").drag_to(page.locator('[data-status="In progress"]'))
    expect(page.locator('[data-status="In progress"] .ticket-card')).to_have_count(1)
    page.get_by_role("button", name="Undo and redo", exact=True).click()
    page.get_by_role("button", name="Undo", exact=True).click()
    expect(page.locator('[data-status="Backlog"] .ticket-card')).to_have_count(1)
    page.get_by_role("button", name="Close history", exact=True).click()
    page.get_by_role("button", name="Preferences", exact=True).click()
    page.get_by_role("switch", name="Work Item Description Scrollable", exact=True).click()
    page.keyboard.press("Escape")
    page.reload()
    page.locator(".ticket-card").click()
    expect(body).to_have_class("nicegui-markdown project-description work-description scrollable")
    assert body.evaluate("el => el.scrollHeight > el.clientHeight && el.clientHeight <= 220")
    page.get_by_role("button", name="Close details", exact=True).click()
    page.get_by_role("button", name="Open HIST project details", exact=True).click()
    row = page.locator(".child-row")
    expect(row.locator(".child-title")).to_contain_text("Agent edit")
    expect(row.locator(".child-status")).to_have_text("Backlog")
    assert row.locator(".child-title").evaluate("el => getComputedStyle(el).textAlign") == "left"
    assert row.locator(".child-status").evaluate("el => getComputedStyle(el).textAlign") == "right"


if __name__ == "__main__":
    main(check)
