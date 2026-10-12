"""Stable presentation ordering; never rewrites item identities or statuses."""

SORT_OPTIONS = {
    "number": "Ticket number",
    "title": "Title",
    "updated": "Recently updated",
}


def ordered_items(items, all_items, order="number"):
    ordered = sorted(items, key=lambda item: (item["project_key"], item["number"]))
    if order == "title":
        return sorted(ordered, key=lambda item: item["title"].casefold())
    if order == "updated":
        return sorted(ordered, key=lambda item: item["updated_at"], reverse=True)
    return ordered
