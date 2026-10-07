import pytest

from organizer import store


@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "test.db"
    store.initialize(path)
    root = store.save(path, {"kind": "Project", "project_key": "TEST", "title": "Test project"})
    return path, root
