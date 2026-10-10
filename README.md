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
not a standalone executable or signed Windows installer. See the [v0.4.0 release notes](docs/releases/v0.4.0.md).

## Local updates and browser refresh

After updated files are installed locally and the app is restarted, an open browser reconnects and
refreshes automatically. A GitHub push alone does not update your local files; the app does not download
updates itself. Save or close editors before updating. An open edited form triggers the browser's
reload warning; choosing to stay keeps the text available to copy, but does not save a draft or restore
the old server session. Saved projects remain in the separate local database.

## What is included

- 24 palettes, each with light and dark appearance, remembered between launches.
- Project colors and name/value tags, with compact cards and expandable details.
- Projects → major goals → minor goals → tasks → subtasks, with optional skipped levels.
- Ideas that do not count toward committed completion totals.
- Stable IDs such as `APP-0001`, including an ID for the project itself.
- Project stages: **Still a Dream, Just Designing, In Progress, On Hold, Completed, Cancelled**.
- Separate task statuses: **Backlog, Ready, In progress, Done, Cancelled**.
- A repository URL on each project. Repository links do not automatically synchronize GitHub issues.
- One work board with project overviews and full/condensed cards.
- Cross-project `blocks` and `relates to` links; unresolved blockers are visibly marked.
- JSON snapshot exchange, standalone HTML reports, and full database backups.
- A [JSON command-line interface for AI agents](docs/agent-interface.md), sharing all UI validation.

Drag a card by its grip to move between status columns, or use its action menu.
Within-column order is by stable ticket number; manual ordering is not saved.
Click a card body or title to open centered details, edit fields, add children, or link related work.
**Condensed view** reduces the board to ticket-number/title rows and remembers your choice.
Selecting a sidebar project replaces the aggregate summary with its description, status, repository,
tags, goal count, active/blocked work and completion progress. **Home** or **My workspace** restores the overview.
Use the menu button to collapse or expand the sidebar; the choice is remembered. Home and Preferences
stay available in the toolbar, and the main panel fills the available browser width.

Projects have an explicit lifecycle: finishing their tasks does **not** automatically mark them
Completed. Completion totals count only the lowest-level committed work once, excluding ideas,
cancelled items, and descendants of cancelled parents. An undivided goal counts as one work item.

## Tags and themes

Edit a project to define its **Project tag defaults**. Every default has a name and a value, or an
explicit **Null** selection. Defaults appear on the project and every work item, including existing
items. Work items can **Override** a default; turn Override off to follow the project again.
Changing a project default updates all items that inherit it. Add extra item-specific pairs with
**Add tag**. **Copy defaults from project → Copy set** reuses another project's set; later edits to
the source set do not change the copy. Filters use the effective name/value pair.

Use **Preferences → Theme palette**, a non-editable dropdown, to select from 24 families. The palette's
source appears between the dropdown and the preview, which stays visible and updates in place.
The toolbar has only **Light / Dark** appearance controls. Former System preferences start in Light.
The original five palettes are joined by 19 authored tonal palettes. All assets remain local.

### Upgrading from 0.1.0 or 0.2.0

Stop the old app before starting the updated version. On first use, the app creates a sibling
`*.pre-v0.3.0-*.db` backup before migrating the database. Old project tags become null-valued project
defaults; old work-item tags become null-valued local tags. Titles, IDs, descriptions, links, preferences,
and activity are retained. Effort is removed from active storage and all interfaces; old values survive
in the backup only. Do not open the migrated database with older code; use the pre-upgrade backup to
roll back. New exports use snapshot version 3; version 1/2 snapshots still import, discarding effort.
Agents must stop writing effort; see the [version 3 contract](docs/agent-interface.md).

### Startup troubleshooting

Launching this version again with the same workspace and port opens the running app. A different
workspace, older app or other program on that port produces a conflict message before database changes.
Close the older app before upgrading; use `-Port 8767` for a separate workspace. Startup output is saved
in `%LOCALAPPDATA%/ProjectOrganize/logs/startup-*.log`. On failure, the launcher prints the exit code and
log location with the underlying error.

## Local data and sharing

On Windows, your data lives outside the repository:

```text
%LOCALAPPDATA%/ProjectOrganize/workspace.db
%LOCALAPPDATA%/ProjectOrganize/demo.db
```

Use `--db "C:/path/to/workspace.db"` to open another workspace. The public source repository does
not contain your working database. The server binds only to `127.0.0.1` and has no network sharing mode.

**Share → Export project snapshot** exports the selected project, or the whole workspace when no
project is selected. Snapshots include descriptions, tags, statuses, and repository URLs.
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

See [product scope](docs/product-scope.md) for the focused project/task workflow and small-update cadence.

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
