from organizer.board_order import SORT_OPTIONS, ordered_items


def test_work_sort_options():
    items = [
        dict(project_key="A", number=n, title=t, updated_at=d)
        for n, t, d in [(10, "apple", "2026-10-10"), (2, "Zoo", "2026-10-12"), (3, "Banana", "2026-10-12")]
    ]
    assert set(SORT_OPTIONS) == {"number", "title", "updated"}
    assert [x["number"] for x in ordered_items(items, [], "title")] == [10, 3, 2]
    assert [x["number"] for x in ordered_items(items, [], "updated")] == [2, 3, 10]
    assert [x["number"] for x in ordered_items(items, [], "number")] == [2, 3, 10]
