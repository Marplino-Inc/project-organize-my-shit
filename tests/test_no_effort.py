import json

import pytest

from organizer.cli import main as cli
from tests.test_store import child


def test_agents_cannot_read_or_write_effort(workspace, capsys):
    path, root = workspace
    with pytest.raises(ValueError, match="read-only fields"):
        child(path, root, effort=2)
    assert cli(["schema"]) == 0
    result = json.loads(capsys.readouterr().out)["data"]
    assert result["api_version"] == 1
    assert "effort" not in result["schema"]["properties"]
