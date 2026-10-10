"""Project feature definitions retain their IDs when their names change."""

from uuid import uuid4

from nicegui import ui


def feature_editor(definitions, used_ids):
    rows = [{"id": key, **value} for key, value in definitions.items()]
    container = ui.column().classes("w-full gap-2")

    def draw():
        container.clear()
        with container:
            for row in rows:
                with ui.column().classes("w-full gap-2 feature-editor-row"):
                    with ui.row().classes("w-full items-center flex-nowrap"):
                        ui.input("Feature name").bind_value(row, "name").props(
                            "outlined dense maxlength=80"
                        ).classes("flex-1")

                        def remove(row=row):
                            rows.remove(row)
                            draw()

                        button = ui.button(icon="close", on_click=remove).props(
                            "flat round dense aria-label='Remove feature'"
                        )
                        if row["id"] in used_ids:
                            button.disable()
                            button.tooltip("Unassign this feature from its work items before removing it.")
                    ui.input("Feature description (optional)").bind_value(row, "description").props(
                        "outlined dense maxlength=2000"
                    ).classes("w-full")
            if not rows:
                ui.label("No features yet. Work items can belong to more than one.").classes("form-hint")

    def add():
        rows.append({"id": str(uuid4()), "name": "", "description": ""})
        draw()

    draw()
    ui.button("Add feature", icon="add", on_click=add).props("flat dense")
    return lambda: {row["id"]: {"name": row["name"], "description": row["description"]} for row in rows}
