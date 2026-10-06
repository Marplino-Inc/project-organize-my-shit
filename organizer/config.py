import os
from pathlib import Path


def database_path(demo=False):
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "ProjectOrganize"
    return root / ("demo.db" if demo else "workspace.db")
