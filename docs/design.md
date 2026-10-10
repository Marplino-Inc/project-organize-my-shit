# Design and scope

## Interface

Use compact, readable notecard surfaces with a restrained five-color project palette. Light mode uses
warm off-white canvas and white cards; dark mode uses slate surfaces and brighter semantic text.
Keep titles neutral and readable. Project accent colors belong on borders, dots, and progress bars.
Named tag pills and status labels supplement color. All drag actions have a menu alternative.

Themes are Light / Dark and persist in SQLite. Palette selection lives in Preferences, with source
attribution above the preview. The main toolbar contains only the appearance toggle.
Use bundled icons, local assets, and system fonts. Avoid remote font or script requests.
Honor reduced-motion preferences and visible focus outlines. Small screens scroll the board itself,
not the whole page; the desktop layout remains the primary target.

The board is the single work view; selecting a project shows its overview above the work items.
Outline, Map and Dashboard were removed in v0.4.0 to keep the daily workflow focused. Cards open centered
details; descriptions stay out of the dense board. The main panel fills the browser width, with a
persistent collapsible sidebar and a toolbar Home button. See [product scope](product-scope.md).

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
or time estimate. Effort estimates were removed in v0.3.0 at the primary user's request.

Charts show matching item counts by status, type, and tag. Tags may overlap. Project completion
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

## v0.2.0 tags and palette library

Project roots hold a default tag map; each item holds only its local pairs/overrides. Reads merge these
maps without duplicating defaults into every child. Null is a value; absence means inherit. Copying a
project's set creates independent defaults. Tags shown in filters, dashboards and reports use the merged
view. Database version 4 adds defaults and migrates old labels after a consistent pre-upgrade backup.

`themes.py` defines semantic interface tokens and five decorative category slots for each palette.
The existing color identity of a project remains stable while its hex accents follow the selected family.
Status labels keep their meaning. Family and light/dark/system preferences are independent. Fonts remain
the existing local system stack; no web font or new frontend dependency is added.

Palette references: [bslib theming](https://rstudio.github.io/bslib/articles/theming/index.html),
[ggplot2 viridis](https://ggplot2.tidyverse.org/reference/scale_viridis.html),
[ggplot2 ColorBrewer](https://ggplot2.tidyverse.org/reference/scale_brewer.html), and
[Google Material color roles](https://m3.material.io/styles/color/roles).
These are adapted UI colors, not full library themes or claims of Material certification. Chart palette
properties do not establish UI contrast; foreground/background pairs and rendered cards are checked separately.

## v0.3.0 feedback decisions — 2026-10-09

Explicit user direction: replace the selected project's summary with a project overview; enlarge card
click targets; center details; offer ticket-number/title-only condensed lanes; remove the card footer
and effort everywhere. Full cards retain tags and blockers; type remains in details, editors, filters
and dashboards. Full is the initial density; the user can persistently switch to Condensed. Global
appearance/share controls remain available in either workspace or project scope.

Effort is removed from the item model and SQLite schema (version 5) after a pre-upgrade backup.
Snapshot/agent contracts advance to version 3; v1/v2 snapshots import while discarding old estimates.

Palette dropdowns remain mounted while CSS tokens update surfaces and accents. Work views redraw
charts, and Preferences keeps a single live preview. The expanded catalog has 24 light/dark families,
including 19 authored tonal palettes. This provides Slack-like variety, not a verified match to Slack's
current inventory: its [official theme guide](https://slack.com/help/articles/205166337-Change-your-Slack-theme)
does not publish a count. The specific count remains an implementation assumption pending user feedback.

## v0.5.0 feedback decisions ? 2026-10-10

The user's marked screenshot calls for empty lanes to end below their message and Add item button,
instead of stretching to match a populated lane. Align lanes at the top and retain a small drop area;
apply the compact treatment in both card densities.

Explicit direction: make fields darker than the canvas and provide a thickness slider. Implementation
choice: mix the active canvas with 6% black for text-field and dropdown surfaces; interpret thickness as
border width, from 1?4 px with a 1 px default. Preserve palette provenance and the accepted card preview.
The preference updates immediately and persists. Rendered field text and labels are checked for 4.5:1
contrast across all 48 theme/mode variants; user acceptance of this adjustment is still pending.

Project-key changes propagate atomically to all items; identity, numbering and links remain stable.
The user explicitly deferred branches, so this update adds no branch settings or prefixes.

## v0.6.0 ? Features

Approved direction: project-scoped Features with optional descriptions and overlapping work-item
membership. Features are explicit assignments independent of the existing parent hierarchy. One item
keeps one identity/status/progress contribution even when it appears under multiple Features.

Use Edit project ? Features to manage definitions, a multi-select in item editors, and one selector
above the existing board, defaulting to All work. Full cards/details show badges; condensed cards stay
unchanged. No new view, workflow or branch prefix. The current palette and typography are preserved.
Naming uses stable feature IDs so labels can change without rewriting assignments. Deleting an assigned
feature is rejected; unassign it first. Browser-tested light/dark screenshots are local test artifacts,
not proof of user acceptance.

## v0.7.0 - Sprig finishing decisions

The user explicitly chose a split Feature band for multiple memberships while retaining the project
band. Color by Feature defaults on (implementation choice); unassigned cards show only their project
band. Both bands default to 5 px, adjustable together from 3-10 px in Preferences. Feature colors
are automatically spaced within the project catalog; catalog changes may rebalance colors. Full-card
badges retain names and corresponding marks. Condensed cards retain ticket/title-only content.
Mouse dragging starts on card bodies, titles or grips, with menu controls excluded; clicking still
opens details. Empty lanes remain compact drop targets. Sprig and its card-and-leaf SVG are the
authorized naming choice; existing data paths and agent contracts remain compatible.

## v1.0.1 - Palette additions

The user requested these additions after the v0.7.0 completion boundary. Remove the decorative
workspace stars tile and expand only the existing palette library. See [theme sources](theme-sources.md)
for the explicit choices, authored adaptations and validation boundary. Version 1.0.1 is user-specified;
no historical release is renamed. Existing preferences, data paths and agent contracts remain intact.
