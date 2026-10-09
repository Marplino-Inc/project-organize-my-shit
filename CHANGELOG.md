# Changelog

## 0.3.0

- Selected projects get a dedicated overview with description, lifecycle, repository, effective tags and progress.
- Click card bodies to open centered details; remove the card footer and add persistent condensed lanes.
- Remove effort from forms, cards, dashboards, reports, SQLite storage and the agent interface.
- Expand to 24 palette families with searchable dropdowns and an in-place preferences preview.
- Reuse matching running instances; diagnose port conflicts before migration and preserve startup logs.
- Database v5 migration backs up the old database. CLI/snapshots use v3; v1/v2 snapshots still import.

## 0.2.0

- Name/value tags with explicit nulls, dynamically inherited project default sets, per-item overrides,
  and copying a default set from another project.
- Effective tag filtering, dashboard groups, details and read-only reports.
- Five palettes with light/dark/system modes: Organize, Shiny Mint, Viridis, Brewer Garden and Material Blue.
- Automatic pre-migration database backup; snapshot v2 with backward import support for v1.
- Breaking agent contract change: tags are objects rather than arrays; CLI v2 includes read-only effective tags.

## 0.1.0

First release for local Windows use.

- Card boards, nested goals/tasks, ideas, stable ticket IDs, tags, and effort estimates.
- Light, dark, and system themes with project colors and accessible card-title contrast.
- Independent project stages, repository links, relationship maps, and fixed dashboards.
- JSON project snapshots, standalone HTML reports, and consistent SQLite backups.
- AI-friendly JSON CLI with shared validation, revision checks, and named item activity.
- Windows launcher, separate demo workspace, and locked dependencies.

Release cleanup rejects malformed agent item references and attempts to change project keys,
and explicitly closes backup database connections after copying.

This release runs locally in a browser. The download contains source and launchers; it requires
uv and a first-run dependency download, and is not a standalone executable or signed installer.
