# Changelog

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
