from playwright.sync_api import expect

from organizer import store
from tests.browser_harness import ROOT, main


def check(page, db):
    description = (
        "## Major Project Goals\n\n- Fix themes\n- Keep settings\n\n" + "Long project note.\n\n" * 25
    )
    description += (
        '<img src=x onerror="window.unsafeMarkdown=true"><script>window.unsafeMarkdown=true</script>'
    )
    store.save(
        db,
        {
            "kind": "Project",
            "project_key": "MARK",
            "title": "Markdown project",
            "description": description,
            "color": "Cyan",
        },
    )
    page.reload()
    page.locator(".project-card").get_by_role("button", name="Markdown project", exact=True).click()
    body = page.locator(".project-description")
    expect(body.locator("h2")).to_have_text("Major Project Goals")
    expect(body.locator("ul li")).to_have_count(2)
    assert body.evaluate("el => el.clientHeight >= el.scrollHeight - 1")
    assert body.bounding_box()["height"] > 220
    assert (
        page.locator(".project-overview .stats").bounding_box()["y"]
        >= body.bounding_box()["y"] + body.bounding_box()["height"]
    )
    assert page.evaluate("window.unsafeMarkdown === undefined")
    expect(body.locator("script, [onerror]")).to_have_count(0)
    page.get_by_role("button", name="Preferences", exact=True).click()
    toggle = page.get_by_role("switch", name="Project Description Scrollable", exact=True)
    expect(toggle).not_to_be_checked()
    toggle.click()
    expect(body).to_have_class("nicegui-markdown project-description scrollable")
    assert body.evaluate("el => el.scrollHeight > el.clientHeight && el.clientHeight <= 220")
    page.keyboard.press("Escape")
    page.reload()
    page.locator(".project-card").get_by_role("button", name="Markdown project", exact=True).click()
    expect(body).to_have_class("nicegui-markdown project-description scrollable")
    page.get_by_role("button", name="Edit project", exact=True).click()
    expect(page.get_by_label("Description", exact=True)).to_have_value(description)
    page.get_by_label("Project symbol", exact=True).click()
    page.get_by_role("option", name="Diamond", exact=True).click()
    page.get_by_role("button", name="Save project", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    expect(page.locator(".project-overview .project-symbol")).to_have_text("diamond")
    expect(page.locator(".sidebar-projects .project-symbol")).to_have_text("diamond")
    assert (
        page.locator(".project-overview .project-symbol").evaluate("el => getComputedStyle(el).color")
        == "rgb(57, 175, 199)"
    )
    assert store.load(db)[0][0]["symbol"] == "diamond"
    page.get_by_role("button", name="Preferences", exact=True).click()
    toggle.click()
    expect(body).not_to_have_class("nicegui-markdown project-description scrollable")
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Dark", exact=True).click()
    expect(body.locator("h2")).to_have_text("Major Project Goals")
    page.set_viewport_size({"width": 600, "height": 850})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    assert body.evaluate("el => el.clientHeight >= el.scrollHeight - 1")
    page.set_viewport_size({"width": 1500, "height": 1080})
    page.screenshot(path=str(ROOT / "artifacts/project-markdown-symbol.png"), full_page=True)


if __name__ == "__main__":
    main(check)
