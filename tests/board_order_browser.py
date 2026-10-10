"""Verify persisted lane sorting and external edits using synthetic records."""

from playwright.sync_api import expect

from organizer import store
from tests.features_browser import main
from tests.test_store import child


def check(page, db):
    project = store.save(
        db,
        {
            "kind": "Project",
            "project_key": "SORT",
            "title": "Sorting",
            "feature_definitions": {
                "a": {"name": "Alpha", "description": ""},
                "z": {"name": "Zebra", "description": ""},
            },
        },
    )
    first = child(db, project, title="Zulu", feature_ids=["z", "a"])
    child(db, project, title="Beta", feature_ids=["z"])
    child(db, project, title="apple")
    page.reload()
    titles = page.locator(".board-column").first.locator(".ticket-title")

    def choose(name):
        page.get_by_label("Sort by", exact=True).click()
        page.get_by_role("option", name=name, exact=True).click()

    expect(titles).to_have_text(["Zulu", "Beta", "apple"])
    choose("Title")
    expect(titles).to_have_text(["apple", "Beta", "Zulu"])
    page.reload()
    expect(page.get_by_label("Sort by", exact=True)).to_have_value("Title")
    expect(titles).to_have_text(["apple", "Beta", "Zulu"])
    choose("Feature")
    expect(titles).to_have_text(["Zulu", "Beta", "apple"])
    first = store.save(db, {"feature_ids": []}, first["id"], first["revision"])
    expect(titles).to_have_text(["Beta", "apple", "Zulu"], timeout=10000)
    choose("Recently updated")
    expect(titles).to_have_text(["Zulu", "Beta", "apple"])
    choose("Title")
    card = page.locator(".ticket-card").filter(has_text="Beta")
    previous_search = page.get_by_label("Search work", exact=True).get_attribute("id")
    card.locator(".ticket-title").drag_to(page.locator(".board-column").nth(1).locator(".ticket-list"))
    expect(titles).to_have_text(["apple", "Zulu"])
    expect(page.locator(".board-column").nth(1).locator(".ticket-title")).to_have_text(["Beta"])
    expect(page.get_by_label("Sort by", exact=True)).to_have_value("Title")
    expect(page.get_by_label("Search work", exact=True)).not_to_have_attribute("id", previous_search)
    page.get_by_label("Search work", exact=True).fill("apple")
    expect(titles).to_have_text(["apple"])
    page.get_by_role("button", name="Clear", exact=True).last.click()
    expect(titles).to_have_text(["apple", "Zulu"])
    assert store.setting(db, "board_sort") == "title"
    assert len(store.load(db)[0]) == 4


if __name__ == "__main__":
    main(check)
