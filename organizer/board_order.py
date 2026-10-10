"""Stable presentation ordering; never rewrites item identities or statuses."""

SORT_OPTIONS = {
    "number": "Ticket number",
    "title": "Title",
    "feature": "Feature",
    "updated": "Recently updated",
}


def ordered_items(items, all_items, order="number"):
    ordered = sorted(items, key=lambda item: (item["project_key"], item["number"]))
    if order == "title":
        return sorted(ordered, key=lambda item: item["title"].casefold())
    if order == "updated":
        return sorted(ordered, key=lambda item: item["updated_at"], reverse=True)
    if order == "feature":
        projects = {item["project_key"]: item for item in all_items if item["kind"] == "Project"}

        def key(item):
            definitions = projects[item["project_key"]]["feature_definitions"]
            names = sorted(definitions[f]["name"].casefold() for f in item["feature_ids"] if f in definitions)
            return (not names, names[0] if names else "", item["title"].casefold())

        return sorted(ordered, key=key)
    return ordered
