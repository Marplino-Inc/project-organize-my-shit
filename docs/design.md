# Design and scope

## Interface

Use compact, readable notecard surfaces with a restrained five-color project palette. Light mode uses
warm off-white canvas and white cards; dark mode uses slate surfaces and brighter semantic text.
Keep titles neutral and readable. Project accent colors belong on borders, dots, and progress bars.
Named tag pills and status labels supplement color. All drag actions have a menu alternative.

Themes are Light / Dark / System and persist in SQLite. System follows the browser's OS preference.
Use bundled icons, local assets, and system fonts. Avoid remote font or script requests.
Honor reduced-motion preferences and visible focus outlines. Small screens scroll the board itself,
not the whole page; the desktop layout remains the primary target.

The main views show the same records: Board (daily flow), Outline (hierarchy), Map (connections),
and Dashboard (summaries). Card titles open detailed panels; descriptions stay out of the dense board.

## Model and reporting

One work-item table stores project roots and their descendants. Each record has a stable internal UUID,
project key, and project-local sequence number. IDs are assigned transactionally and never reused.
No hard delete is exposed; cancellation retains history and references.

Hierarchy: Project → Major goal → Minor goal → Task → Subtask. Ideas are terminal items, convertible
to tasks when committed. Levels can be skipped. A project has a repository URL and independent lifecycle.
Cross-project links are separate rows, not additional parents.

Completion counts committed leaf work once, using the hierarchy before any per-ticket dashboard filter.
Cancelled work and descendants of cancelled parents are excluded; ideas are excluded. An undivided goal
is itself leaf work. Goal/project acceptance status remains explicit. Count-based progress is not an effort
or time estimate. Effort values are ordinal 1–5; T-shirt labels are another presentation of the same values.

Charts show matching item counts by status, type, tag, and effort. Tags may overlap. Project completion
cards use the selected project scope; task filters affect the work views and charts, not those cards.

## Architecture

- `store.py`: SQL, migrations, validation, revision checks, snapshots, and backups.
- `views.py` and `styles.css`: NiceGUI presentation and appearance tokens.
- `cli.py`: structured JSON interface for agents, using the same store functions.
- `reports.py`: escaped, standalone HTML reports.
- `demo.py`: explicitly selected sample records in a separate database.

The service binds to loopback. A browser UI is a local frontend, not cloud hosting.
SQLite transactions serialize writes from the UI and agents. Revision checks reject stale item edits.
Snapshot imports validate first, then commit all records together. Imports create new internal IDs and
reject project-key collisions. There is no multi-user synchronization service.

## Research informing the design

These are inspirations and framework capabilities, not claims of formal project-management certification:

- [Atlassian: Kanban](https://www.atlassian.com/agile/kanban/) — visualize ongoing work and limit overload.
- [Jira work items](https://support.atlassian.com/jira-software-cloud/docs/what-is-a-work-item/) — IDs and hierarchy.
- [Jira relationships](https://support.atlassian.com/jira-software-cloud/docs/link-issues/) — explicit cross-project links.
- [Trello labels](https://support.atlassian.com/trello/docs/adding-labels-to-cards/) — concise, named card categories.
- [NiceGUI dark mode](https://nicegui.io/documentation/dark_mode) — explicit and system appearance.
- [NiceGUI sortable containers](https://nicegui.io/documentation/sortable) — supported cross-column dragging.
- [SQLite intended uses](https://sqlite.org/whentouse.html) — embedded local storage and portable snapshots.

No Jira or Trello code or assets are bundled.
