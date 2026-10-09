"""Explicitly selected sample workspace. Never seeded into a personal workspace."""

from . import store


def seed(path):
    if store.load(path)[0]:
        return

    def project(key, title, color, description):
        return store.save(
            path,
            dict(
                kind="Project",
                project_key=key,
                title=title,
                color=color,
                description=description,
                status="In Progress",
                tag_defaults={"workspace": "demo", "release": None},
            ),
        )

    def item(parent, title, kind="Task", status="Ready", tags=None, **extra):
        return store.save(
            path,
            dict(
                project_key=parent["project_key"],
                parent_id=parent["id"],
                title=title,
                kind=kind,
                status=status,
                tags={"area": ", ".join(tags)} if tags else {},
                color=parent["color"],
                **extra,
            ),
        )

    workspace = project(
        "ORG",
        "A calmer project workspace",
        "Violet",
        "Turn a scattered collection of ideas into a clear, colorful place to make progress.",
    )
    store.save(
        path,
        {"repository_url": "https://github.com/Marplino-Inc/project-organize-my-shit"},
        workspace["id"],
        workspace["revision"],
    )
    addon = project("TIP", "Better tooltips", "Teal", "A focused addon with readable, useful tooltips.")
    mod = project(
        "MOD",
        "A little more adventure",
        "Coral",
        "A small game mod with thoughtful quality-of-life features.",
    )
    store.save(path, {"status": "Still a Dream"}, mod["id"], mod["revision"])
    appearance = item(workspace, "Make the workspace feel like home", "Major goal", tags=["design"])
    theme = item(
        appearance,
        "Design light & dark palettes",
        status="Done",
        tags=["design", "accessibility"],
        description="Use readable surfaces, deliberate accents, and named states.",
    )
    item(
        appearance,
        "Give every project its own color",
        status="In progress",
        tags=["design"],
        description="Project colors should remain recognizable in both themes.",
    )
    item(
        workspace,
        "Build the project relationship map",
        status="In progress",
        tags=["visualization"],
        description="Show how features connect without crowding the canvas.",
    )
    item(workspace, "Export a progress report", tags=["sharing"])
    item(
        workspace,
        "Keyboard shortcuts for quick capture",
        "Idea",
        status="Backlog",
        tags=["usability"],
    )
    fonts = item(addon, "Readable text, anywhere", "Major goal", tags=["appearance"])
    item(fonts, "Choose a tooltip font", status="Ready", tags=["appearance"])
    item(
        fonts,
        "Check contrast in the game client",
        status="Backlog",
        tags=["accessibility"],
        blocked="Needs an in-game test session.",
    )
    item(addon, "Save the font selection", status="Done", tags=["settings"])
    item(mod, "Sketch the first encounter", status="Backlog", tags=["design"])
    item(mod, "Write a tiny installation guide", status="Ready", tags=["docs"])
    store.add_link(path, theme["id"], fonts["id"], "relates to")
    store.add_link(path, workspace["id"], addon["id"], "relates to")
