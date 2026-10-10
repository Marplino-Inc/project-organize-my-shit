from organizer.board_order import ordered_items


def test_numeric_title_feature_and_recent_order():
    root = dict(
        kind="Project",
        project_key="A",
        feature_definitions={
            "z": {"name": "Zebra"},
            "a": {"name": "alpha"},
        },
    )

    def task(number, title, features, date):
        return dict(project_key="A", number=number, title=title, feature_ids=features, updated_at=date)

    items = [
        task(10, "apple", [], "2026-10-10T12:00:00"),
        task(2, "Zoo", ["z", "a"], "2026-10-10T13:00:00"),
        task(3, "Banana", ["z"], "2026-10-10T13:00:00"),
    ]

    def numbers(order):
        return [item["number"] for item in ordered_items(items, [root], order)]

    assert numbers("number") == [2, 3, 10]
    assert numbers("title") == [10, 3, 2]
    assert numbers("feature") == [2, 3, 10]
    assert numbers("updated") == [2, 3, 10]
    assert numbers("unknown") == [2, 3, 10]
    root["feature_definitions"]["a"]["name"] = "zzzz"
    assert numbers("feature") == [3, 2, 10]
    assert [item["number"] for item in items] == [10, 2, 3]
