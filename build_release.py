"""Build a reviewable source ZIP from an explicit allowlist; never bundle workspace data."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "sprig-work-1.0.0-work"
ROOT_FILES = {
    "README.md",
    "AGENTS.md",
    "AGENT_HANDOFF.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "Setup.command",
    "Start.command",
    "Start.ps1",
    "Start.cmd",
    "sprig-cli",
    "main.py",
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
    "build_release.py",
    ".gitignore",
    ".gitattributes",
}
DOCS = {
    "docs/work-agent-interface.md",
    "docs/branch-maintenance.md",
    "docs/releases/v1.0.0-work.md",
    "docs/game-themes.md",
    "docs/theme-sources.md",
}


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    selected = sorted(
        path
        for path in tracked
        if path
        and (
            path in ROOT_FILES
            or path in DOCS
            or path.startswith(("organizer/", "tests/", "docs/security/", ".github/"))
        )
    )
    assert ROOT_FILES <= set(selected), "Commit all package sources before packaging"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *selected], cwd=ROOT, check=True)
    manifest = {"release": "v1.0.0-work", "commit": commit, "files": {}}
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    archive = output / f"{NAME}-source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative in selected:
            path = ROOT / relative
            assert path.resolve().is_relative_to(ROOT) and not path.is_symlink()
            assert path.suffix not in {".db", ".sqlite", ".sqlite3", ".env"}
            raw = path.read_bytes()
            manifest["files"][relative] = hashlib.sha256(raw).hexdigest()
            entry = zipfile.ZipInfo(f"{NAME}/{relative}", date_time=(2026, 10, 12, 0, 0, 0))
            entry.create_system = 3
            mode = 0o100755 if relative.endswith(".command") or relative == "sprig-cli" else 0o100644
            entry.external_attr = mode << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, raw)
        bundle.writestr(f"{NAME}/SOURCE-MANIFEST.json", json.dumps(manifest, indent=2))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    print(f"Packaged {len(selected)} source/evidence files: {archive}")


if __name__ == "__main__":
    main()
