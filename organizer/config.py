import os
import sys
from pathlib import Path


def database_path(demo=False):
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "SprigWork"
    elif sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SprigWork"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "SprigWork"
    return root / ("demo.db" if demo else "workspace.db")
