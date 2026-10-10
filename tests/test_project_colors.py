import pytest

from organizer import store, themes


@pytest.mark.parametrize("color", list(store.COLORS)[5:])
def test_new_project_colors_round_trip(workspace, tmp_path, color):
    path, root = workspace
    store.save(path, {"color": color}, root["id"], root["revision"])
    target = tmp_path / "colors.db"
    store.initialize(target)
    store.import_snapshot(target, store.export_snapshot(path))
    assert store.load(target)[0][0]["color"] == color
    for family in themes.FAMILIES:
        assert themes.project_colors(family)[color] == store.COLORS[color]
        assert f"--project-{color}:{store.COLORS[color]}" in themes.css(family)
