import json

import pytest

from organizer import store
from organizer.cli import main


@pytest.mark.parametrize("field,value", [("feature_ids", []), ("feature_definitions", {}), ("features", {})])
def test_work_edition_rejects_removed_fields(workspace, field, value):
    path, root = workspace
    before = store.load(path)
    with pytest.raises(ValueError, match="Unknown"):
        store.save(path, {field: value}, root["id"], root["revision"])
    assert store.load(path) == before


def test_schema_and_exports_have_no_feature_fields(workspace, capsys):
    path, root = workspace
    assert main(["schema"]) == 0
    schema = json.loads(capsys.readouterr().out)["data"]
    assert schema["edition"] == "sprig-work"
    assert "feature" not in json.dumps(schema).lower()
    exported = store.export_snapshot(path)
    assert "feature" not in exported.lower()
    assert json.loads(exported)["format"] == "sprig-work-snapshot"
