"""Structured tag inputs. An absent override is different from an explicit null."""

from nicegui import ui


def tag_editor(values, defaults=None, *, prefix="Tag"):
    local = [
        {"name": name, "value": value or "", "null": value is None}
        for name, value in values.items()
        if name not in (defaults or {})
    ]
    inherited = {}
    defaults = dict(defaults or {})
    for name, value in defaults.items():
        chosen = values.get(name, value)
        inherited[name] = {
            "name": name,
            "value": chosen or "",
            "null": chosen is None,
            "override": name in values,
        }
    container = ui.column().classes("w-full gap-2 tag-editor")

    def draw():
        container.clear()
        with container:
            for row in list(inherited.values()) + local:
                is_inherited = row["name"] in inherited and row is inherited[row["name"]]
                with ui.element("div").classes("tag-input-row"):
                    if is_inherited:
                        with ui.column().classes("gap-0"):
                            ui.label(row["name"]).classes("text-sm font-bold")
                            ui.label("Project default").classes("form-hint")

                        def override_changed(event, row=row):
                            if not event.value:
                                value = defaults[row["name"]]
                                row["value"], row["null"] = value or "", value is None

                        ui.switch("Override", value=row["override"], on_change=override_changed).bind_value(
                            row, "override"
                        ).props("dense")
                    else:
                        ui.input(prefix + " name").bind_value(row, "name").props(
                            "outlined dense maxlength=40"
                        )
                    field = (
                        ui.input(prefix + " value")
                        .bind_value(row, "value")
                        .props("outlined dense maxlength=200")
                    )
                    null = ui.checkbox("Null").bind_value(row, "null").props("dense")
                    if is_inherited:
                        null.bind_enabled_from(row, "override")
                        field.bind_enabled_from(
                            row, "override", backward=lambda value, row=row: value and not row["null"]
                        )
                        # Either source changing recomputes the combined enabled state.
                        field.bind_enabled_from(
                            row, "null", backward=lambda value, row=row: not value and row["override"]
                        )
                    else:
                        field.bind_enabled_from(row, "null", backward=lambda value: not value)

                        def remove(row=row):
                            local.remove(row)
                            draw()

                        ui.button(icon="close", on_click=remove).props(
                            "flat round dense aria-label='Remove tag row'"
                        )
            if not local and not inherited:
                ui.label("No tags yet. Add a name and a value, or select Null.").classes("form-hint")

    def add():
        local.append({"name": "", "value": "", "null": False})
        draw()

    draw()
    ui.button("Add default tag" if prefix == "Default tag" else "Add tag", icon="add", on_click=add).props(
        "flat dense"
    )

    def read():
        result = {}
        for row in list(inherited.values()) + local:
            if "override" in row and not row["override"]:
                continue
            name = row["name"].strip().casefold()
            if not name:
                raise ValueError("Every tag needs a name. Remove unused rows.")
            if name in result:
                raise ValueError(f"Duplicate tag name: {name}")
            result[name] = None if row["null"] else row["value"]
        return result

    def replace(values):
        local[:] = [
            {"name": name, "value": value or "", "null": value is None} for name, value in values.items()
        ]
        inherited.clear()
        draw()

    def update_defaults(new_defaults):
        values = read()
        defaults.clear()
        defaults.update(new_defaults)
        local[:] = [
            {"name": name, "value": value or "", "null": value is None}
            for name, value in values.items()
            if name not in defaults
        ]
        inherited.clear()
        for name, value in defaults.items():
            chosen = values.get(name, value)
            inherited[name] = {
                "name": name,
                "value": chosen or "",
                "null": chosen is None,
                "override": name in values,
            }
        draw()

    return read, replace, update_defaults
