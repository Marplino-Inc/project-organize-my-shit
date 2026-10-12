# Sprig Work - v1.0.0-work

Personal, single-user project/task tracking. Based on Sprig 1.2.0 at daf2b10, with work-item Features
removed from UI, data model, CLI, sorting and reports. Other workflows remain: hierarchy, tags,
Markdown, themes, symbols, sorting, five-step UI undo/redo, snapshots and local CLI.

## Apple Silicon Mac setup (including M4)

Requires macOS 13+, employer-approved uv and initial internet access. Python 3.12 and locked packages
are installed into a local virtualenv. This is a source package, not a signed/notarized .app.
Extract into a local non-synced folder, then in Terminal:

```sh
cd "/path/to/sprig-work-1.0.0-work"
sh Setup.command
sh Start.command
```

Open http://127.0.0.1:8775. Keep the terminal open; Ctrl+C stops the app. Browser closure alone does not.
Run `sh Start.command --demo --port 8776` for fictional sample data. No admin access or login service.
After setup, launch/CLI use the existing virtualenv directly without dependency downloads.
Data: `~/Library/Application Support/SprigWork/workspace.db`. Windows uses `%LOCALAPPDATA%/SprigWork`;
Linux uses `$XDG_DATA_HOME/SprigWork` or `~/.local/share/SprigWork`. Personal data formats are rejected.
Windows users may run Start.ps1; its setup uses uv. Work and personal instances use different ports.

## Agent handoff

Open this package in VS Code with your approved Copilot account/model and read [AGENT_HANDOFF.md](AGENT_HANDOFF.md).
The package includes repository instructions and a JSON CLI, without a model key, AI SDK or MCP server.

```sh
sh sprig-cli schema
sh sprig-cli projects
sh sprig-cli items --project APP
```

[Work CLI contract](docs/work-agent-interface.md). Copilot may send command output/context to its model
provider; local storage does not make AI inference local. Follow employer data policies and tool approvals.

## Security, sharing and maintenance

Read [SECURITY.md](SECURITY.md) and [release notes](docs/releases/v1.0.0-work.md).
Reports/exports/backups are manual plaintext files. Full backups include activity and undo history.
Protect files with OS permissions, FileVault and approved storage. No tamper-proof audit-log claim.
The release contains no personal workspace, credentials, .venv or Git history.

Main and work are active branches; shared improvements should reach both, except work-item Features.
v1.0.0-work is a fixed release point. Analytics/mapping are deferred. [Maintenance rule](docs/branch-maintenance.md).
Historical personal-edition documents in Git are background only; this README and work docs are current.

## Validation

```sh
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run playwright install chromium
uv run python -m tests.work_browser
uv run python -m tests.history_browser
uv run python -m tests.project_overview_browser
```

Pinned runtime packages/hashes are in requirements.txt; full resolution is in uv.lock. Inventory and
security scan evidence are in docs/security. See release notes for actual platform evidence and limits.
