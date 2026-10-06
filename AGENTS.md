# Project development

- Local Windows application, Python + NiceGUI + SQLite. No hosted service required.
- Public repository: never commit working databases, exports, private project data, or personal profile notes.
- Share through project snapshots and standalone read-only reports. Concurrent shared editing is outside v0.1.
- Projects have a repository URL and independent lifecycle (Still a Dream / Just Designing / In Progress / On Hold / Completed / Cancelled).
- Agent updates use the documented JSON CLI and the same validation as the UI. Preserve revision checks and named activity.
- UI quality is a product requirement: deliberate color, compact cards, and complete light/dark/system themes.
- Preserve semantic text alongside color; provide keyboard alternatives to drag and drop.
- Keep application rules in plain Python functions and SQL, separate from NiceGUI widgets.
- Parent-child hierarchy and cross-project relationships are distinct. Never double-count parent and child work.
- Snapshot import must validate before writing, be atomic, and never silently overwrite an existing project.
- Use uv sync --locked, uv run pytest, and browser checks for UI behavior. Distinguish automated checks from user acceptance.
- Do not claim installer packaging, performance, or visual acceptance without testing them.
