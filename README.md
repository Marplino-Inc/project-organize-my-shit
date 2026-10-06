# Organize

A local project workspace with colorful cards, nested goals, and a little room for ideas.

Built with **Python, NiceGUI, and SQLite**. The interface runs in your browser at
`http://127.0.0.1:8765`; the application and database stay on your computer.
No account, cloud database, or remote service is required.

## Run on Windows

For the release download, extract the Windows source ZIP and double-click **Start.cmd**.
This starts the same local application as the PowerShell commands below; it requires uv.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone this repository,
and run these PowerShell commands from the checkout:

```powershell
uv sync --locked --no-dev
uv run --no-dev python main.py
```

The browser opens automatically. Keep the terminal running; press **Ctrl+C** there to stop.
The first installation requires internet access. Normal operation uses bundled local assets.

Or run `./Start.ps1`. For a separate sample workspace on port 8766, run `./Start.ps1 -Demo` or:

```powershell
uv run --no-dev python main.py --demo --port 8766
```

Demo edits persist separately from your own projects. This is a source-based application,
not a standalone executable or signed Windows installer. See the [v0.1.0 release notes](docs/releases/v0.1.0.md).

## What is included

- Light, dark, and system appearance, remembered between launches.
- Project colors and named tags, with compact cards and expandable details.
- Projects → major goals → minor goals → tasks → subtasks, with optional skipped levels.
- Ideas that do not count toward committed completion totals.
- Stable IDs such as `APP-0001`, including an ID for the project itself.
- Project stages: **Still a Dream, Just Designing, In Progress, On Hold, Completed, Cancelled**.
- Separate task statuses: **Backlog, Ready, In progress, Done, Cancelled**.
- Optional effort: **XS–XL** or **1–5**. Labels can change in Preferences; estimates retain their level.
- A repository URL on each project. Repository links do not automatically synchronize GitHub issues.
- Board, hierarchy outline, relationship map, and dashboard views.
- Cross-project `blocks` and `relates to` links; unresolved blockers are visibly marked.
- JSON snapshot exchange, standalone HTML reports, and full database backups.
- A [JSON command-line interface for AI agents](docs/agent-interface.md), sharing all UI validation.

Drag a card by its grip to move between status columns, or use its action menu.
Within-column order is by stable ticket number; manual ordering is not saved.
Click a card title to read the description, edit fields, add children, or link related work.

Projects have an explicit lifecycle: finishing their tasks does **not** automatically mark them
Completed. Completion totals count only the lowest-level committed work once, excluding ideas,
cancelled items, and descendants of cancelled parents. An undivided goal counts as one work item.
Effort is an ordered estimate, not hours or a percentage weight.

## Local data and sharing

On Windows, your data lives outside the repository:

```text
%LOCALAPPDATA%/ProjectOrganize/workspace.db
%LOCALAPPDATA%/ProjectOrganize/demo.db
```

Use `--db "C:/path/to/workspace.db"` to open another workspace. The public source repository does
not contain your working database. The server binds only to `127.0.0.1` and has no network sharing mode.

**Share → Export project snapshot** exports the selected project, or the whole workspace when no
project is selected. Snapshots include descriptions, tags, statuses, estimates, and repository URLs.
Relationships to excluded projects are omitted and counted; export the whole workspace to retain
cross-project relationships. Import previews the file, validates it, and creates separate projects.
It never overwrites an existing key. For a single-project snapshot, supply a new key to import a copy.
This is snapshot exchange, not concurrent synchronization.

**Share → Download read-only report** produces a standalone, script-free HTML file that opens offline.
Use your browser's Print command to save it as PDF.

**Preferences → Download workspace backup** makes a consistent SQLite backup of all records,
preferences, and activity. To restore, stop the app, keep a copy of the backup, and run:

```powershell
uv run --no-dev python main.py --db "C:/Backups/organize-backup.db"
```

The selected backup becomes the working database. Project snapshots omit local preferences and activity;
use a database backup when you need the entire workspace.

## Development

```powershell
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run playwright install chromium
uv run python -m tests.browser_smoke
```

The browser checks use a temporary database and write screenshots to ignored `artifacts/`.
See [development status](docs/development-status.md) for validation and known limits,
and [design decisions](docs/design.md) for the UI and data model.
