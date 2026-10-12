"""Exercise the source archive in a clean folder; use native launchers on macOS."""

import hashlib
import json
import platform
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.request import urlopen


def main():
    root = Path(__file__).resolve().parents[1]
    archive = root / "artifacts/sprig-work-1.0.0-work-source.zip"
    with tempfile.TemporaryDirectory(prefix="Sprig Work Package ") as folder:
        target = Path(folder)
        with zipfile.ZipFile(archive) as bundle:
            assert all(".git/" not in name and not name.endswith(".db") for name in bundle.namelist())
            bundle.extractall(target)
        app = target / "sprig-work-1.0.0-work"
        manifest = json.loads((app / "SOURCE-MANIFEST.json").read_text())
        for relative, digest in manifest["files"].items():
            assert hashlib.sha256((app / relative).read_bytes()).hexdigest() == digest
        if sys.platform == "darwin":
            subprocess.run(["sh", "Setup.command"], cwd=app, check=True)
            command = ["sh", "sprig-cli"]
            start = ["sh", "Start.command"]
        else:
            command = [sys.executable, "-m", "organizer.cli"]
            start = [sys.executable, "main.py"]
        db = target / "sample work.db"

        def cli(*args):
            result = subprocess.run(
                command + ["--db", str(db), *args], cwd=app, check=True, text=True, capture_output=True
            )
            return json.loads(result.stdout)["data"]

        assert cli("schema")["edition"] == "sprig-work"
        payload = target / "project.json"
        payload.write_text(json.dumps({"kind": "Project", "project_key": "PKG", "title": "Package test"}))
        project = cli("create", "--file", str(payload))
        payload.write_text(
            json.dumps({"kind": "Task", "project_key": "PKG", "parent_id": "PKG-0001", "title": "Task"})
        )
        task = cli("create", "--file", str(payload))
        payload.write_text('{"status":"Done"}')
        cli("update", "PKG-0002", "--revision", str(task["revision"]), "--file", str(payload))
        assert cli("get", "PKG-0002")["status"] == "Done"
        assert cli("get", "PKG-0001")["id"] == project["id"]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        log = target / "server.log"
        with log.open("w") as output:
            process = subprocess.Popen(
                start + ["--db", str(db), "--port", str(port), "--no-browser"],
                cwd=app,
                stdout=output,
                stderr=output,
            )
            try:
                for _ in range(100):
                    try:
                        with urlopen(f"http://127.0.0.1:{port}/_organize/instance", timeout=1) as response:
                            assert json.load(response)["app"] == "sprig-work"
                        break
                    except OSError:
                        if process.poll() is not None:
                            raise AssertionError(log.read_text())
                        time.sleep(0.1)
                else:
                    raise AssertionError("Packaged server did not start")
            finally:
                process.terminate()
                process.wait(timeout=15)
        print(
            json.dumps({"package_test": "passed", "system": platform.system(), "machine": platform.machine()})
        )


if __name__ == "__main__":
    main()
