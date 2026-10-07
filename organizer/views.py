"""NiceGUI presentation. Widgets call the shared store used by the agent CLI."""

import json
import tempfile
from collections import Counter
from pathlib import Path

from nicegui import ui

from . import store, themes
from .reports import html_report
from .tag_editor import tag_editor

STATUS_COLORS = {
    "Backlog": "#9b96b0",
    "Ready": "#6299e8",
    "In progress": "#d99a30",
    "Done": "#24a99a",
    "Cancelled": "#ed7d75",
}
ICONS = {
    "Project": "folder_open",
    "Major goal": "flag",
    "Minor goal": "outlined_flag",
    "Task": "check_box_outline_blank",
    "Subtask": "subdirectory_arrow_right",
    "Idea": "lightbulb_outline",
}


def register(path, demo=False):
    @ui.page("/")
    def workspace():
        client = ui.context.client
        ui.add_css((Path(__file__).parent / "styles.css").read_text(encoding="utf-8"))
        ui.colors(primary="#7053c1", secondary="#24a99a", positive="#087e6e", negative="#b04447")
        preference = store.setting(path, "theme", "System")
        dark = ui.dark_mode({"Light": False, "Dark": True, "System": None}[preference])
        palette = store.setting(path, "palette", "organize")
        if palette not in themes.FAMILIES:
            palette = "organize"
        theme_style = ui.html("<style>" + themes.css(palette) + "</style>", sanitize=False).classes("hidden")
        state = {
            "project": None,
            "stage": None,
            "view": "Board",
            "search": "",
            "tag": None,
            "kind": None,
            "status": None,
            "effort": None,
            "blocked": False,
            "expanded": False,
            "signature": None,
        }
        data = {"items": [], "links": []}
        effort_scale = store.setting(path, "effort_scale", "T-shirt")

        def signature(items, links):
            return (
                tuple((x["id"], x["revision"]) for x in items),
                tuple(sorted((x["source"], x["target"], x["kind"]) for x in links)),
            )

        def refresh():
            data["items"], data["links"] = store.load(path)
            state["signature"] = signature(data["items"], data["links"])
            navigation.refresh()
            content.refresh()

        def choose_project(key):
            state["project"] = key
            state["stage"] = None
            refresh()

        def change_filter(key, value):
            state[key] = value
            work_area.refresh()

        def change_view(view):
            state["view"] = view
            content.refresh()

        def selected_items():
            projects = {
                x["project_key"]
                for x in data["items"]
                if x["kind"] == "Project"
                and (not state["project"] or x["project_key"] == state["project"])
                and (not state["stage"] or x["status"] == state["stage"])
            }
            return [x for x in data["items"] if x["project_key"] in projects]

        def filtered_items():
            search = state["search"].strip().casefold()
            return [
                x
                for x in selected_items()
                if (not state["kind"] or x["kind"] == state["kind"])
                and (not state["tag"] or state["tag"] in store.tag_options([x], data["items"]))
                and (not state["status"] or x["status"] == state["status"])
                and (state["effort"] is None or x["effort"] == state["effort"])
                and (not state["blocked"] or is_blocked(x))
                and (
                    not search
                    or search
                    in (
                        store.ticket(x)
                        + " "
                        + x["title"]
                        + " "
                        + x["description"]
                        + " "
                        + " ".join(store.tag_text(n, v) for n, v in tags_for(x).items())
                    ).casefold()
                )
            ]

        def is_blocked(item):
            by_id = {x["id"]: x for x in data["items"]}
            return bool(
                item["blocked"]
                or any(
                    link["kind"] == "blocks"
                    and link["target"] == item["id"]
                    and by_id[link["source"]]["status"] not in ("Done", "Completed", "Cancelled")
                    for link in data["links"]
                )
            )

        def effort_label(value):
            return store.EFFORT[value] if effort_scale == "T-shirt" or value is None else str(value)

        def tags_for(item):
            return store.effective_tags(item, data["items"])

        def project_color(item):
            root = next(
                (
                    x
                    for x in data["items"]
                    if x["kind"] == "Project" and x["project_key"] == item["project_key"]
                ),
                item,
            )
            return themes.project_colors(palette)[root["color"]]

        def tag_label(name, value):
            index = sum(map(ord, name)) % 5
            ui.label(store.tag_text(name, value)).classes("tag structured-tag").style(
                f"--tag-accent:var(--palette-{index})"
            )

        def change_palette(value):
            nonlocal palette
            palette = value
            store.set_setting(path, "palette", value)
            theme_style.set_content("<style>" + themes.css(value) + "</style>")
            refresh()

        def change_theme(value):
            dark.value = {"Light": False, "Dark": True, "System": None}[value]
            store.set_setting(path, "theme", value)

        def update_status(item, status):
            try:
                store.save(path, {"status": status}, item["id"], item["revision"])
                ui.notify(f"{store.ticket(item)} → {status}", type="positive")
            except ValueError as error:
                ui.notify(str(error), type="negative")
            refresh()

        def edit_dialog(item=None, project=False, parent=None, status="Backlog"):
            all_items, _ = store.load(path)
            roots = {x["project_key"]: x for x in all_items if x["kind"] == "Project"}
            is_project = project or (item and item["kind"] == "Project")
            if not is_project and not roots:
                edit_dialog(project=True)
                return
            initial = item or {}
            key = (
                initial.get("project_key")
                or (parent and parent["project_key"])
                or state["project"]
                or next(iter(roots), "")
            )
            with client.layout, ui.dialog() as dialog, ui.card().classes("dialog-card"):
                ui.label(
                    ("Edit " + store.ticket(item))
                    if item
                    else ("New project" if is_project else "New work item")
                ).classes("dialog-heading")
                ui.label("A clear title now. Room for the details whenever you need them.").classes(
                    "form-hint"
                )
                title = (
                    ui.input("Title", value=initial.get("title", ""))
                    .props("outlined autofocus maxlength=200")
                    .classes("w-full")
                )
                if is_project:
                    with ui.element("div").classes("form-row"):
                        key_input = ui.input("Project key", value=initial.get("project_key", "")).props(
                            "outlined hint='2–10 letters/numbers; e.g. TOOL'"
                        )
                        color = ui.select(
                            list(store.COLORS), label="Project color", value=initial.get("color", "Violet")
                        ).props("outlined")
                    if item:
                        key_input.disable()
                    repo = (
                        ui.input(
                            "Repository URL (optional)",
                            value=initial.get("repository_url", ""),
                            placeholder="https://github.com/organization/repository",
                        )
                        .props("outlined")
                        .classes("w-full")
                    )
                    project_select = kind_select = parent_select = None
                else:
                    with ui.element("div").classes("form-row"):
                        project_select = ui.select(
                            {k: f"{k} · {v['title']}" for k, v in roots.items()}, label="Project", value=key
                        ).props("outlined")
                        default_kind = "Subtask" if parent and parent["kind"] == "Task" else "Task"
                        kind_select = ui.select(
                            list(store.KINDS[1:]), label="Type", value=initial.get("kind", default_kind)
                        ).props("outlined")
                    if item:
                        project_select.disable()
                    parent_select = (
                        ui.select({}, label="Parent", value=None).props("outlined").classes("w-full")
                    )

                    def update_parents():
                        options = {
                            x["id"]: f"{store.ticket(x)} · {x['title']}"
                            for x in all_items
                            if x["project_key"] == project_select.value
                            and store.RANK[x["kind"]] < store.RANK[kind_select.value]
                            and (not item or x["id"] != item["id"])
                        }
                        chosen = parent_select.value or initial.get("parent_id") or (parent and parent["id"])
                        parent_select.set_options(
                            options, value=chosen if chosen in options else roots[project_select.value]["id"]
                        )

                    project_select.on_value_change(update_parents)
                    kind_select.on_value_change(update_parents)
                    update_parents()
                with ui.element("div").classes("form-row"):
                    status_select = ui.select(
                        list(store.PROJECT_STATUSES if is_project else store.STATUSES),
                        label="Status",
                        value=initial.get("status", "Still a Dream" if is_project else status),
                    ).props("outlined")
                    estimate = ui.select(
                        {0: "Not estimated", **{n: effort_label(n) for n in range(1, 6)}},
                        label="Effort",
                        value=initial.get("effort") or 0,
                    ).props("outlined")
                    if is_project:
                        estimate.disable()
                    elif kind_select:

                        def estimate_state():
                            estimate.set_enabled(kind_select.value != "Major goal")
                            if kind_select.value == "Major goal":
                                estimate.value = 0

                        kind_select.on_value_change(estimate_state)
                        estimate_state()
                description = (
                    ui.textarea("Description", value=initial.get("description", ""))
                    .props("outlined autogrow")
                    .classes("w-full")
                )
                if is_project:
                    ui.label("Project tag defaults").classes("eyebrow")
                    ui.label(
                        "Applied to this project and all its work items. Items can override a value or explicitly use null."
                    ).classes("form-hint")
                    read_defaults, replace_defaults, _ = tag_editor(
                        initial.get("tag_defaults", {}), prefix="Default tag"
                    )
                    with ui.row().classes("w-full items-center"):
                        copy_from = (
                            ui.select(
                                {
                                    k: f"{k} · {v['title']}"
                                    for k, v in roots.items()
                                    if not item or v["id"] != item["id"]
                                },
                                label="Copy defaults from project",
                            )
                            .props("outlined dense")
                            .classes("flex-1")
                        )
                        ui.button(
                            "Copy set",
                            on_click=lambda: (
                                replace_defaults(roots[copy_from.value]["tag_defaults"])
                                if copy_from.value
                                else None
                            ),
                        ).props("flat")
                    if initial.get("tags"):
                        ui.label("Project-only overrides").classes("eyebrow")
                        read_tags, _, _ = tag_editor(initial["tags"])
                    else:

                        def read_tags():
                            return {}
                else:
                    ui.label("Tags").classes("eyebrow")
                    ui.label(
                        "Inherited defaults stay linked to the project. Override to set a different value or null."
                    ).classes("form-hint")
                    read_tags, _, update_defaults = tag_editor(
                        initial.get("tags", {}), roots[project_select.value]["tag_defaults"]
                    )

                    def update_tag_project():
                        try:
                            update_defaults(roots[project_select.value]["tag_defaults"])
                        except ValueError as error:
                            ui.notify(str(error), type="negative")

                    project_select.on_value_change(update_tag_project)
                blocked = (
                    ui.input("Blocked reason (optional)", value=initial.get("blocked", ""))
                    .props("outlined")
                    .classes("w-full")
                )
                error_label = ui.label().classes("error-text")

                def save_item():
                    try:
                        tags = read_tags()
                        defaults = read_defaults() if is_project else {}
                    except ValueError as error:
                        error_label.text = str(error)
                        return
                    fields = dict(
                        title=title.value,
                        description=description.value,
                        status=status_select.value,
                        tags=tags,
                        tag_defaults=defaults,
                        blocked=blocked.value,
                        effort=estimate.value or None,
                    )
                    if is_project:
                        fields.update(
                            kind="Project",
                            project_key=key_input.value,
                            color=color.value,
                            repository_url=repo.value.strip(),
                        )
                    else:
                        fields.update(
                            kind=kind_select.value,
                            project_key=project_select.value,
                            parent_id=parent_select.value,
                        )
                    try:
                        saved = store.save(
                            path, fields, item["id"] if item else None, item["revision"] if item else None
                        )
                    except ValueError as error:
                        error_label.text = str(error)
                        return
                    dialog.close()
                    ui.notify(f"Saved {store.ticket(saved)}", type="positive")
                    refresh()

                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save project" if is_project else "Save item", on_click=save_item).classes(
                        "primary-button"
                    )
            dialog.open()

        def detail(item):
            items, links = store.load(path)
            item = next(x for x in items if x["id"] == item["id"])
            by_id = {x["id"]: x for x in items}
            with (
                client.layout,
                ui.dialog().props("position=right full-height") as dialog,
                ui.card().classes("dialog-card detail-card"),
            ):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(f"{store.ticket(item)} · {item['kind']}").classes("project-key")
                    ui.button(icon="close", on_click=dialog.close).props(
                        "flat round dense aria-label='Close details'"
                    )
                ui.label(item["title"]).classes("dialog-heading")
                with ui.row().classes("gap-2"):
                    ui.label(item["status"]).classes("tag")
                    ui.label("Effort: " + effort_label(item["effort"])).classes("tag")
                    for name, value in store.effective_tags(item, items).items():
                        tag_label(name, value)
                if item["repository_url"]:
                    ui.link("Open repository ↗", item["repository_url"], new_tab=True).classes(
                        "repo-link"
                    ).props("rel=noopener")
                parent = by_id.get(item["parent_id"])
                if parent:
                    ui.label(f"Under {store.ticket(parent)} · {parent['title']}").classes("form-hint")
                if item["blocked"]:
                    ui.label("Blocked: " + item["blocked"]).classes("blocked")
                ui.label(item["description"] or "No description yet.").classes("detail-description")

                def edit():
                    dialog.close()
                    edit_dialog(item)

                with ui.row().classes("gap-2"):
                    ui.button("Edit item", icon="edit", on_click=edit).classes("primary-button")
                    if store.RANK[item["kind"]] < 4:

                        def add_child():
                            dialog.close()
                            edit_dialog(parent=item)

                        ui.button("Add child", icon="add", on_click=add_child).classes("secondary-button")
                children = [x for x in items if x["parent_id"] == item["id"]]
                if children:
                    ui.separator()
                    ui.label(f"Children · {len(children)}").classes("eyebrow")
                    for child in children:

                        def open_child(child=child):
                            dialog.close()
                            detail(child)

                        ui.button(f"{store.ticket(child)} · {child['title']}", on_click=open_child).props(
                            "flat no-caps"
                        ).classes("w-full justify-start")
                ui.separator()
                ui.label("Relationships").classes("eyebrow")
                related = [x for x in links if item["id"] in (x["source"], x["target"])]
                for link in related:
                    other = by_id[link["target"] if link["source"] == item["id"] else link["source"]]
                    label = (
                        "blocked by"
                        if link["kind"] == "blocks" and link["target"] == item["id"]
                        else link["kind"]
                    )
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(f"{label} {store.ticket(other)} · {other['title']}").classes("text-sm")

                        def unlink(link=link):
                            store.remove_link(path, link)
                            dialog.close()
                            refresh()
                            detail(item)

                        ui.button(icon="link_off", on_click=unlink).props(
                            "flat round dense aria-label='Remove relationship'"
                        )
                if not related:
                    ui.label("Connect this item to work in any project.").classes("form-hint")
                with ui.row().classes("w-full items-end no-wrap"):
                    link_kind = (
                        ui.select(["blocks", "relates to"], value="relates to", label="Relationship")
                        .props("outlined dense")
                        .classes("w-36")
                    )
                    link_target = (
                        ui.select(
                            {
                                x["id"]: f"{store.ticket(x)} · {x['title']}"
                                for x in items
                                if x["id"] != item["id"]
                            },
                            label="Other item",
                            with_input=True,
                        )
                        .props("outlined dense")
                        .classes("flex-1")
                    )

                    def link_item():
                        try:
                            store.add_link(path, item["id"], link_target.value, link_kind.value)
                        except ValueError as error:
                            ui.notify(str(error), type="negative")
                            return
                        dialog.close()
                        refresh()
                        detail(item)

                    ui.button(icon="add_link", on_click=link_item).props("flat aria-label='Add relationship'")
                with ui.expansion("Recent activity", icon="history").classes("w-full"):
                    for event in store.activity(path, item["id"]):
                        fields = ", ".join(json.loads(event["fields"]))
                        ui.label(
                            f"{event['actor']} {event['action']} · {event['timestamp']} · {fields}"
                        ).classes("form-hint")
                ui.label(f"Updated {item['updated_at']} · Revision {item['revision']}").classes("form-hint")
            dialog.open()

        def sharing():
            project = state["project"]
            with client.layout, ui.dialog() as dialog, ui.card().classes("dialog-card"):
                ui.label("Share a little progress").classes("dialog-heading")
                ui.label("Export scope: " + (project or "All projects")).classes("form-hint")
                ui.label(
                    "Snapshots include descriptions, tags, and repository links. Check your project content before sharing."
                ).classes("form-hint")

                def download_snapshot():
                    raw = store.export_snapshot(path, project)
                    omitted = json.loads(raw)["omitted_external_links"]
                    ui.download.content(raw, f"organize-{project or 'workspace'}.json", "application/json")
                    if omitted:
                        ui.notify(
                            f"{omitted} relationship(s) to other projects omitted. Export all projects to retain them.",
                            type="warning",
                        )

                def download_report():
                    items, _ = store.load(path)
                    included = [x for x in items if not project or x["project_key"] == project]
                    ui.download.content(
                        html_report(included, effort_scale),
                        f"organize-{project or 'workspace'}-report.html",
                        "text/html",
                    )

                ui.button("Export project snapshot", icon="download", on_click=download_snapshot).classes(
                    "primary-button"
                )
                ui.button("Download read-only report", icon="description", on_click=download_report).classes(
                    "secondary-button"
                )
                ui.label(
                    "Reports open in a browser and can be printed to PDF. Snapshots can be imported into Organize."
                ).classes("form-hint")
                ui.separator()
                ui.label("Import a snapshot").classes("eyebrow")
                ui.label(
                    "Imports create separate projects. Existing project keys are never overwritten."
                ).classes("form-hint")
                new_key = (
                    ui.input("New key (optional, single-project imports)")
                    .props("outlined dense")
                    .classes("w-full")
                )
                import_state = {"raw": None}
                import_message = ui.label().classes("form-hint")

                async def upload(event):
                    import_state["raw"] = None
                    import_button.disable()
                    try:
                        raw = await event.file.read()
                        snapshot = store.parse_snapshot(raw)
                        import_state["raw"] = raw
                        projects = [x for x in snapshot.items if x.kind == "Project"]
                        import_message.text = f"Ready: {len(projects)} project(s), {len(snapshot.items)} items, {len(snapshot.links)} relationships."
                        if snapshot.omitted_external_links:
                            import_message.text += f" {snapshot.omitted_external_links} external relationships were excluded by the exporter."
                        import_button.enable()
                    except ValueError as error:
                        import_message.text = "Cannot import: " + str(error)

                ui.upload(
                    label="Choose snapshot (.json)",
                    on_upload=upload,
                    auto_upload=True,
                    max_file_size=10_000_000,
                    on_rejected=lambda: ui.notify("Choose a JSON snapshot under 10 MB.", type="negative"),
                ).props("accept=.json flat bordered").classes("w-full")

                def import_data():
                    try:
                        count = store.import_snapshot(path, import_state["raw"], new_key.value or None)
                    except ValueError as error:
                        import_message.text = str(error)
                        return
                    dialog.close()
                    refresh()
                    ui.notify(f"Imported {count} items", type="positive")

                with ui.row().classes("w-full justify-end"):
                    ui.button("Close", on_click=dialog.close).props("flat")
                    import_button = ui.button("Import snapshot", on_click=import_data).classes(
                        "primary-button"
                    )
                    import_button.disable()
            dialog.open()

        def settings_dialog():
            nonlocal effort_scale
            with client.layout, ui.dialog() as dialog, ui.card().classes("dialog-card"):
                ui.label("Workspace preferences").classes("dialog-heading")
                ui.label("Palette library").classes("eyebrow")
                ui.label(
                    "Each palette supports Light, Dark, and System. Preview it on your actual board; switch back at any time."
                ).classes("form-hint")
                with ui.element("div").classes("palette-grid"):
                    for key, theme in themes.FAMILIES.items():
                        with ui.element("div").classes("palette-choice"):
                            ui.label(theme["name"]).classes("font-bold")
                            with ui.row().classes("gap-1"):
                                for color in theme["colors"]:
                                    ui.element("span").classes("palette-swatch").style(
                                        "background:" + color
                                    ).tooltip(color)
                            ui.label(theme["description"]).classes("form-hint")
                            ui.button(
                                "Use " + theme["name"], on_click=lambda key=key: change_palette(key)
                            ).props("flat dense")
                            if theme["url"]:
                                ui.link(theme["source"], theme["url"], new_tab=True).classes("repo-link")
                ui.separator()
                ui.label("Effort labels").classes("eyebrow")
                ui.label(
                    "Both choices use the same five ordered levels. Changing labels preserves estimates; levels are not hours."
                ).classes("form-hint")

                def update_scale(event):
                    nonlocal effort_scale
                    effort_scale = event.value
                    store.set_setting(path, "effort_scale", event.value)
                    refresh()

                ui.toggle(["T-shirt", "1–5"], value=effort_scale, on_change=update_scale)
                ui.separator()
                ui.label("Backup").classes("eyebrow")
                ui.label(
                    "A complete SQLite backup includes all projects, relationships, preferences, and activity."
                ).classes("form-hint")

                def download_backup():
                    with tempfile.TemporaryDirectory() as directory:
                        output = Path(directory) / "organize-backup.db"
                        store.backup(path, output)
                        ui.download.content(
                            output.read_bytes(), "organize-backup.db", "application/octet-stream"
                        )

                ui.button("Download workspace backup", icon="save_alt", on_click=download_backup).classes(
                    "secondary-button"
                )
                ui.label(
                    "To open a backup, close the app and launch with --db pointing to the backup file. Keep an untouched copy."
                ).classes("form-hint")
                ui.button("Done", on_click=dialog.close).classes("primary-button self-end")
            dialog.open()

        @ui.refreshable
        def navigation():
            with ui.element("aside").classes("sidebar"):
                with ui.element("div").classes("brand"):
                    ui.icon("dashboard_customize", size="25px").classes("brand-mark")
                    with ui.column().classes("gap-0"):
                        ui.label("organize").classes("brand-name")
                        ui.label("ROOM FOR YOUR IDEAS").style("font-size:8px;letter-spacing:1px").classes(
                            "muted"
                        )
                ui.button(
                    "My workspace", icon="space_dashboard", on_click=lambda: choose_project(None)
                ).props("flat").classes("w-full " + ("nav-active" if state["project"] is None else ""))
                with ui.column().classes("sidebar-projects w-full gap-2"):
                    ui.label("Projects").classes("eyebrow px-2")
                    for root in (x for x in data["items"] if x["kind"] == "Project"):
                        with (
                            ui.button(on_click=lambda key=root["project_key"]: choose_project(key))
                            .props("flat")
                            .classes(
                                "w-full " + ("nav-active" if root["project_key"] == state["project"] else "")
                            )
                        ):
                            ui.element("span").classes("status-dot").style(
                                "background:" + project_color(root)
                            )
                            ui.label(root["title"]).classes("ellipsis text-xs")
                    ui.button("New project", icon="add", on_click=lambda: edit_dialog(project=True)).props(
                        "flat"
                    ).classes("w-full muted")
                with ui.column().classes("sidebar-bottom w-full gap-2"):
                    ui.button("Preferences", icon="tune", on_click=settings_dialog).props("flat").classes(
                        "w-full muted"
                    )
                    ui.label("Yours. On this computer.").classes("text-xs muted px-2")
                    if demo:
                        ui.label("Demo workspace").classes("demo-label")

        def stat(value, label, icon, color):
            with ui.element("div").classes("stat"):
                with ui.element("div"):
                    ui.label(str(value)).classes("stat-value")
                    ui.label(label).classes("stat-label")
                ui.icon(icon, size="22px").classes("stat-icon").style("color:" + color)

        def render_card(item, cards):
            by_id = {x["id"]: x for x in data["items"]}
            with (
                ui.element("article")
                .classes("ticket-card")
                .style("--project-color:" + project_color(item)) as card
            ):
                cards[card.id] = item
                with ui.element("div").classes("ticket-top"):
                    ui.label(store.ticket(item)).classes("ticket-id")
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("drag_indicator").classes("drag-handle").tooltip(
                            "Drag to another status column"
                        )
                        with ui.button(icon="more_horiz").props(
                            f"flat dense round size=xs aria-label='Actions for {store.ticket(item)}'"
                        ):
                            with ui.menu():
                                for status in store.STATUSES:
                                    ui.menu_item(
                                        "Move to " + status,
                                        on_click=lambda s=status, i=item: update_status(i, s),
                                    )
                ui.button(item["title"], on_click=lambda: detail(item)).props("flat no-caps").classes(
                    "ticket-title"
                )
                parent = by_id.get(item["parent_id"])
                if parent:
                    ui.label(parent["title"]).classes("ticket-context")
                with ui.element("div").classes("tags"):
                    effective = tags_for(item)
                    for name, value in list(effective.items())[:3]:
                        tag_label(name, value)
                    if len(effective) > 3:
                        ui.label(f"+{len(effective) - 3}").classes("tag")
                if is_blocked(item):
                    with ui.element("div").classes("blocked"):
                        ui.icon("block", size="13px")
                        ui.label("Blocked").tooltip(item["blocked"] or "An unfinished item blocks this work.")
                with ui.element("div").classes("ticket-footer"):
                    with ui.row().classes("gap-1 items-center"):
                        ui.icon(ICONS[item["kind"]], size="14px")
                        ui.label(item["kind"])
                    ui.label(effort_label(item["effort"]) if item["effort"] else "—").classes(
                        "effort"
                    ).tooltip("Effort: " + effort_label(item["effort"]))

        def board(items):
            items = [x for x in items if x["kind"] != "Project"]
            containers, cards = {}, {}

            def dropped(event):
                item = cards[event.item.id]
                target = containers[event.target.id]
                if item["status"] != target:
                    update_status(item, target)

            statuses = list(store.STATUSES[:4])
            if state["status"] == "Cancelled":
                statuses = ["Cancelled"]
            with ui.element("div").classes("board"):
                for status in statuses:
                    matches = [x for x in items if x["status"] == status]
                    with ui.element("section").classes("board-column").props(f"aria-label='{status} column'"):
                        with ui.element("div").classes("column-header"):
                            ui.element("span").classes("status-dot").style(
                                "background:" + STATUS_COLORS[status]
                            )
                            ui.label(status)
                            ui.label(str(len(matches))).classes("count")
                        with ui.column().classes("ticket-list").props(f"data-status='{status}'") as column:
                            containers[column.id] = status
                            for item in matches:
                                render_card(item, cards)
                        column.make_sortable(
                            group="board", on_end=dropped, handle=".drag-handle", options={"sort": False}
                        )
                        if not matches:
                            ui.label("A little room for what's next.").classes("empty-column")
                        ui.button(
                            "Add item", icon="add", on_click=lambda s=status: edit_dialog(status=s)
                        ).props("flat").classes("add-card")

        def outline(items):
            by_id = {x["id"]: x for x in data["items"]}
            visible_ids = {x["id"] for x in items}
            context_ids = set(visible_ids)
            for item in items:
                cursor = by_id.get(item["parent_id"])
                while cursor:
                    context_ids.add(cursor["id"])
                    cursor = by_id.get(cursor["parent_id"])

            def branch(parent_id=None, depth=0):
                for item in (
                    x for x in data["items"] if x["parent_id"] == parent_id and x["id"] in context_ids
                ):
                    with (
                        ui.element("div").classes("outline-row").style(f"margin-left:{min(depth, 4) * 20}px")
                    ):
                        ui.icon(ICONS[item["kind"]], size="18px").style("color:" + project_color(item))
                        ui.label(store.ticket(item)).classes("ticket-id")
                        ui.button(item["title"], on_click=lambda x=item: detail(x)).props(
                            "flat dense"
                        ).classes("flex-1")
                        ui.label(item["status"] if item["id"] in visible_ids else "Parent context").classes(
                            "tag"
                        )
                    branch(item["id"], depth + 1)

            branch()

        def graph(items):
            included = (
                items if state["expanded"] else [x for x in items if x["kind"] in ("Project", "Major goal")]
            )
            if not included:
                ui.label("No nodes match. Try including tasks or clearing filters.").classes("muted")
                return
            included = included[:150]
            ids = {x["id"] for x in included}
            nodes = [
                {
                    "id": x["id"],
                    "name": store.ticket(x) + "\n" + x["title"][:30],
                    "value": store.ticket(x),
                    "symbolSize": 44 if x["kind"] == "Project" else 26,
                    "itemStyle": {"color": project_color(x)},
                    "label": {"show": True, "position": "bottom"},
                }
                for x in included
            ]
            edges = [
                {
                    "source": x["parent_id"],
                    "target": x["id"],
                    "value": "contains",
                    "lineStyle": {"color": "#aaa5bb", "type": "solid"},
                }
                for x in included
                if x["parent_id"] in ids
            ]
            edges += [
                {
                    "source": x["source"],
                    "target": x["target"],
                    "value": x["kind"],
                    "symbol": ["none", "arrow" if x["kind"] == "blocks" else "none"],
                    "lineStyle": {
                        "color": "#d99a30" if x["kind"] == "blocks" else "#8b70ef",
                        "type": "dashed",
                        "curveness": 0.15,
                    },
                }
                for x in data["links"]
                if x["source"] in ids and x["target"] in ids
            ]

            def node_click(event):
                if event.data_type == "node":
                    detail(included[event.data_index])

            with ui.element("div").classes("graph-shell"):
                ui.echart(
                    {
                        "animation": False,
                        "tooltip": {"show": False},
                        "series": [
                            {
                                "type": "graph",
                                "layout": "force",
                                "roam": True,
                                "draggable": True,
                                "data": nodes,
                                "links": edges,
                                "force": {"repulsion": 650, "edgeLength": 140},
                                "lineStyle": {"width": 2},
                                "emphasis": {"focus": "adjacency"},
                            }
                        ],
                    },
                    on_point_click=node_click,
                    renderer="svg",
                ).classes("w-full h-[460px]")
                ui.label(
                    "Solid: parent / child · Dashed violet: related · Dashed amber arrow: blocks · Drag to arrange; click to open."
                ).classes("graph-legend")
            ui.label(
                "Showing up to 150 matching nodes. Narrow the project or tag filter for larger workspaces."
            ).classes("form-hint mt-3")
            with ui.expansion("Browse map items with the keyboard", icon="list").classes("w-full"):
                for item in included:
                    ui.button(
                        store.ticket(item) + " · " + item["title"], on_click=lambda x=item: detail(x)
                    ).props("flat dense")

        def dashboard(items):
            tickets = [x for x in items if x["kind"] != "Project"]
            with ui.element("div").classes("dashboard-grid"):

                def distribution(title, counts, filter_key, palette):
                    with ui.element("section").classes("panel"):
                        ui.label(title).classes("text-base font-bold mb-3")
                        maximum = max(counts.values(), default=1) or 1
                        for index, (label, count) in enumerate(counts.items()):
                            with ui.element("div").classes("distribution"):

                                def drill(label=label):
                                    state[filter_key] = label
                                    state["view"] = "Board"
                                    content.refresh()

                                text = (
                                    store.tag_options(tickets, data["items"]).get(label, str(label))
                                    if filter_key == "tag"
                                    else str(label)
                                )
                                ui.button(text, on_click=drill).props("flat dense")
                                with ui.element("div").classes("distribution-track"):
                                    ui.element("div").style(
                                        f"height:100%;width:{100 * count / maximum}%;background:{palette[index % len(palette)]};border-radius:5px"
                                    )
                                ui.label(str(count)).classes("text-xs muted")

                distribution(
                    "Work by status",
                    {s: sum(x["status"] == s for x in tickets) for s in store.STATUSES},
                    "status",
                    list(STATUS_COLORS.values()),
                )
                distribution(
                    "Work by type",
                    dict(Counter(x["kind"] for x in tickets)),
                    "kind",
                    themes.FAMILIES[palette]["colors"],
                )
                distribution(
                    "Work by tag",
                    dict(Counter(tag for x in tickets for tag in store.tag_options([x], data["items"]))),
                    "tag",
                    themes.FAMILIES[palette]["colors"],
                )
                with ui.element("section").classes("panel"):
                    ui.label("Effort distribution").classes("text-base font-bold mb-3")
                    counts = Counter(x["effort"] for x in tickets)
                    for effort in (None, 1, 2, 3, 4, 5):
                        with ui.row().classes("w-full justify-between mb-3"):
                            ui.label(effort_label(effort)).classes("text-sm muted")
                            ui.label(str(counts[effort])).classes("text-sm")
                    ui.label(
                        "Ordered estimates, not hours. Tags overlap, so tag counts can exceed the item total."
                    ).classes("form-hint")
            ui.label(
                "Charts count matching work items by level. Completion cards above count only committed leaf work in the selected project scope."
            ).classes("form-hint mt-4")

        @ui.refreshable
        def work_area():
            items = filtered_items()
            count = sum(
                x["kind"] != "Project"
                and (state["view"] != "Board" or x["status"] != "Cancelled" or state["status"] == "Cancelled")
                for x in items
            )
            ui.label(
                f"{count} matching work items"
                + (
                    " · Cancelled items hidden"
                    if state["view"] == "Board" and state["status"] != "Cancelled"
                    else ""
                )
            ).classes("form-hint mb-3")
            if state["view"] == "Board":
                board(items)
            elif state["view"] == "Outline":
                outline(items)
            elif state["view"] == "Map":
                graph(items)
            else:
                dashboard(items)

        @ui.refreshable
        def content():
            roots = [x for x in data["items"] if x["kind"] == "Project"]
            selected = next((x for x in roots if x["project_key"] == state["project"]), None)
            with ui.element("div").classes("topbar"):
                with ui.element("div").classes("breadcrumbs"):
                    ui.icon("home", size="16px")
                    ui.label("Workspace")
                    ui.label("/")
                    ui.label(selected["project_key"] if selected else "Overview")
                    if demo:
                        ui.label("Demo").classes("demo-label")
                with ui.row().classes("items-center gap-3"):
                    ui.select(
                        {key: value["name"] for key, value in themes.FAMILIES.items()},
                        label="Palette",
                        value=palette,
                        on_change=lambda event: change_palette(event.value),
                    ).props("outlined dense").classes("w-44")
                    ui.toggle(
                        ["Light", "Dark", "System"],
                        value=store.setting(path, "theme", "System"),
                        on_change=lambda e: change_theme(e.value),
                    ).props("unelevated toggle-color=primary").classes("theme-toggle")
                    ui.button(icon="refresh", on_click=refresh).props(
                        "flat round dense aria-label='Refresh workspace'"
                    ).tooltip("Refresh workspace")
                    ui.button("Share", icon="ios_share", on_click=sharing).props("flat").classes(
                        "secondary-button"
                    )
            with ui.element("div").classes("hero"):
                with ui.element("div"):
                    ui.html(
                        "<h1>"
                        + ("Your ideas. Taking shape." if not selected else "Your project, in focus.")
                        + "</h1>"
                    )
                    ui.label(
                        selected["title"]
                        if selected
                        else "A little structure. More room to make things happen."
                    ).classes("muted text-sm")
                    if selected and selected["repository_url"]:
                        ui.link("Open repository ↗", selected["repository_url"], new_tab=True).classes(
                            "repo-link"
                        ).props("rel=noopener")
                with ui.element("div").classes("hero-symbol"):
                    ui.icon("auto_awesome", size="34px")
            scope = selected_items()
            leaves = store.active_leaves(scope)
            done, total = store.progress(scope)
            with ui.element("div").classes("stats"):
                stat(
                    sum(x["kind"] == "Project" for x in scope),
                    "Projects in scope",
                    "folder_open",
                    "var(--accent)",
                )
                stat(
                    sum(x["status"] == "In progress" for x in leaves),
                    "Work in progress",
                    "timelapse",
                    "var(--warning)",
                )
                stat(f"{done}/{total}", "Work items completed", "task_alt", "var(--positive)")
                stat(
                    sum(is_blocked(x) and x["status"] not in ("Done", "Cancelled") for x in leaves),
                    "Blocked work items",
                    "block",
                    "var(--negative)",
                )
            if not roots:
                with ui.element("div").classes("empty-state"):
                    ui.icon("dashboard_customize", size="45px").style("color:var(--accent)")
                    ui.html("<h2>Give your next idea a home.</h2>")
                    ui.label(
                        "Start a project, break it into a few goals, and make your first move. Everything stays on this computer."
                    )
                    ui.button(
                        "Create your first project", icon="add", on_click=lambda: edit_dialog(project=True)
                    ).classes("primary-button")
                    ui.button("Import a project", icon="file_upload", on_click=sharing).props("flat")
                return
            with ui.element("div").classes("section-title"):
                ui.html("<h2>" + ("Project overview" if selected else "Your projects") + "</h2>")

                def filter_stage(event):
                    state["stage"] = event.value
                    content.refresh()

                ui.select(
                    list(store.PROJECT_STATUSES),
                    label="Project stage",
                    value=state["stage"],
                    on_change=filter_stage,
                ).props("outlined dense clearable").classes("w-48 ml-auto mr-3")
                ui.button("New project", icon="add", on_click=lambda: edit_dialog(project=True)).props(
                    "flat dense"
                ).classes("text-xs muted")
            with ui.element("div").classes("project-grid"):
                for project in [
                    x
                    for x in ([selected] if selected else roots)
                    if not state["stage"] or x["status"] == state["stage"]
                ]:
                    items = [x for x in data["items"] if x["project_key"] == project["project_key"]]
                    done, total = store.progress(items)
                    with (
                        ui.element("div")
                        .classes("project-card")
                        .style("--project-color:" + project_color(project))
                    ):
                        with ui.row().classes("w-full justify-between items-center"):
                            ui.label(store.ticket(project)).classes("project-key")
                            ui.button(icon="open_in_new", on_click=lambda x=project: detail(x)).props(
                                f"flat round dense size=xs aria-label='Open {project['project_key']} project details'"
                            )
                        ui.button(
                            project["title"], on_click=lambda key=project["project_key"]: choose_project(key)
                        ).props("flat").classes("project-title")
                        ui.label(project["status"]).classes("tag self-start mt-2")
                        with ui.element("div").classes("progress-track"):
                            ui.element("div").classes("progress-fill").style(
                                f"width:{100 * done / total if total else 0}%"
                            )
                        with ui.row().classes("w-full justify-between text-xs muted"):
                            ui.label(f"{done} of {total} work items done").tooltip(
                                "Counts the lowest-level committed work once. Parent goals, ideas, and cancelled work are excluded."
                            )
                            ui.label(f"{round(100 * done / total)}%" if total else "No planned work")
            with ui.element("div").classes("workspace-panel"):
                with ui.row().classes("w-full justify-between items-center"):
                    with ui.element("div").classes("view-tabs"):
                        for name, icon in (
                            ("Board", "view_kanban"),
                            ("Outline", "account_tree"),
                            ("Map", "hub"),
                            ("Dashboard", "bar_chart"),
                        ):
                            ui.button(name, icon=icon, on_click=lambda name=name: change_view(name)).props(
                                "flat"
                            ).classes("selected" if state["view"] == name else "")
                    ui.button("New item", icon="add", on_click=edit_dialog).classes("primary-button")
                with ui.element("div").classes("filters"):
                    search = (
                        ui.input(
                            "Search work",
                            value=state["search"],
                            on_change=lambda e: change_filter("search", e.value or ""),
                        )
                        .props("outlined dense debounce=250 clearable")
                        .classes("search")
                    )
                    with search.add_slot("prepend"):
                        ui.icon("search", size="18px")
                    ui.select(
                        store.tag_options(selected_items(), data["items"]),
                        label="Tag",
                        with_input=True,
                        value=state["tag"],
                        on_change=lambda e: change_filter("tag", e.value),
                    ).props("outlined dense clearable")
                    ui.select(
                        list(store.KINDS),
                        label="Type",
                        value=state["kind"],
                        on_change=lambda e: change_filter("kind", e.value),
                    ).props("outlined dense clearable")
                    ui.select(
                        list(store.STATUSES),
                        label="Status",
                        value=state["status"],
                        on_change=lambda e: change_filter("status", e.value),
                    ).props("outlined dense clearable")
                    ui.checkbox(
                        "Blocked",
                        value=state["blocked"],
                        on_change=lambda e: change_filter("blocked", e.value),
                    ).props("dense")
                    if state["view"] == "Map":
                        ui.checkbox(
                            "Include tasks",
                            value=state["expanded"],
                            on_change=lambda e: change_filter("expanded", e.value),
                        ).props("dense")

                    def clear_filters():
                        state.update(search="", tag=None, kind=None, status=None, effort=None, blocked=False)
                        content.refresh()

                    ui.button("Clear", on_click=clear_filters).props("flat dense").classes("text-xs muted")
                work_area()

        data["items"], data["links"] = store.load(path)
        state["signature"] = signature(data["items"], data["links"])
        with ui.element("div").classes("shell"):
            navigation()
            with ui.element("main").classes("main"):
                content()

        def check_external_updates():
            items, links = store.load(path)
            if signature(items, links) != state["signature"]:
                refresh()

        ui.timer(3, check_external_updates)
