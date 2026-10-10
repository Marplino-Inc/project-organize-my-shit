# Project development

- Local Windows application, Python + NiceGUI + SQLite. No hosted service required.
- Public repository: never commit working databases, exports, private project data, or personal profile notes.
- Share through project snapshots and standalone read-only reports. Concurrent shared editing is outside v0.1.
- Projects have a repository URL and independent lifecycle (Still a Dream / Just Designing / In Progress / On Hold / Completed / Cancelled).
- Agent updates use the documented JSON CLI and the same validation as the UI. Preserve revision checks and named activity.
- UI quality is a product requirement: deliberate color, compact cards, and complete light/dark themes. Palette selection and provenance live in Preferences; preserve its accepted example.
- Preserve semantic text alongside color; provide keyboard alternatives to drag and drop.
- Keep application rules in plain Python functions and SQL, separate from NiceGUI widgets.
- Parent-child hierarchy and cross-project relationships are distinct. Never double-count parent and child work.
- Snapshot import must validate before writing, be atomic, and never silently overwrite an existing project.
- Use uv sync --locked, uv run pytest, and browser checks for UI behavior. Distinguish automated checks from user acceptance.
- Do not claim installer packaging, performance, or visual acceptance without testing them.

## Product scope

The core job is tracking projects and tasks: create, find, update, and retain work. Keep a single board
and project overview. Outline, Map and Dashboard were explicitly removed in v0.4.0; do not restore them
or add analytics/integrations without a new user request. Existing relationship records remain intact.

Propose one coherent improvement per update, usually one to three small changes, with a concrete user
benefit and an acceptance example. Explain what should wait and why; implementation capacity alone is
not a reason to add features. Honor explicit larger batches. Keep commits focused and include relevant
tests/docs with their change. No new approval gate is implied.

For a new product, 0.1.0 should be the smallest usable project/task lifecycle. A future 1.0.0 should make
that core dependable through real use, recovery, clear errors and installation/update evidence, with
only a few justified additions. This app already has published versions; move forward without renumbering
history. See docs/product-scope.md for the current boundary and follow-up cadence.
