# Development status

## v1.2.0 - Markdown and project symbols

- Render project descriptions as sanitized Markdown while retaining editable Markdown source.
- Expand the project overview description by default; add persistent Project Description Scrollable preference.
- Add ten project symbols using the selected project color in sidebar, overview and workspace cards.
- Add agent-editable symbol field (CLI contract 6), database schema 7 with pre-migration backup,
  and snapshot format 5 with import support for formats 1-4.

Validation: 181 pytest checks passed. A dedicated browser workflow verified headings/bullets,
HTML sanitization, expanded flow, scrolling preference persistence, unchanged Markdown in the editor,
symbol selection and project-color rendering. Migration backups and legacy imports have automated
coverage. These checks use isolated workspaces, not personal data or user acceptance.

## v1.1.0 - Game styles, lane sorting and project colors

Implemented six explicitly requested full style presets with game-name labels, both modes and
stronger visual character. Existing palettes and the selected default remain. Added persistent
within-lane ordering by ticket number, title, Feature and update time, plus twelve project colors
with swatches. New color values require 1.1.0+ importers; database and JSON structures are unchanged.

Validation: 170 pytest checks and Ruff passed. The full browser workflow passed all 100 palette/mode
combinations. Dedicated game-style checks covered both densities, keyboard opening, dragging, narrow
screens, saved selection and removing the style when switching back. Sorting browser checks covered
all four orders, persistence, external membership updates, filtered views and status dragging.
Project-color checks covered twelve options, actual band color and persistence; new colors round-trip
through snapshots. Representative Persona, Halo, Alien and WoW screenshots and color swatches were
visually inspected. These are automated/inspection results, not user acceptance or full accessibility
conformance. Styles use original local CSS and system font fallbacks.
The Windows ZIP passed launch/conflict checks and persisted World of Warcraft styling, Cyan project
color, band/field preferences and Title sorting across restart. The unsaved-editor warning timed out
once; a diagnostic rerun passed with an active user gesture and visible dirty editor logged. This
is an intermittent existing check, not a fixed defect or draft-recovery guarantee.


## v1.0.1 - Expanded palettes

Removed the decorative workspace stars tile. Added 20 palette families: GGplot Gray Pastel, all
16 shinythemes variants, Apple HIG, Microsoft Fluent and IBM Carbon. There are now 44 families /
88 Light-Dark variants, all within the existing Preferences dropdown and live preview. Existing
settings, data paths and agent contracts remain compatible; no database migration. Version 1.0.1
is explicitly requested, following 0.7.0 without inventing an intervening release.

Validation: 150 pytest checks and Ruff passed. The full Chromium suite passed all 88 variants,
including rendered card/field contrast, darker field surfaces, source links, selection persistence,
CRUD, lane dragging, external updates, exports and responsive layouts. GGplot Gray Pastel light,
Apple HIG light and Carbon dark screenshots were inspected. Pure/near-black source foundations
were adjusted where needed to keep the established darker-field treatment.
The Windows source ZIP passed clean extraction, Start.cmd, duplicate-launch reuse, port-conflict
diagnostics, saved data/theme/border persistence, automatic reconnect and unsaved-edit warning.
These are automated checks and visual inspection, not user acceptance or a full accessibility audit.


## v0.7.0 - Sprig

The app is now Sprig, with an original local card-and-leaf logo. Repository/module names,
data paths, snapshot identifiers and agent commands remain compatible. No database migration.
Color by Feature defaults on, with one front-band segment per assigned Feature and the project
band retained. Unassigned items retain only the project band. Preferences saves a shared 3-10 px
band width, default 5 px. Card bodies and titles support lane dragging; status menus remain available.

Validation: 110 pytest checks and Ruff passed. The full Chromium suite passed all 48 themes.
The dedicated Feature/Sprig workflow verified segmented bands, toggle and width persistence,
both card densities, body/title dragging into empty lanes, ordinary clicks and retained memberships.
Light/dark screenshots were inspected. The Windows source ZIP passed launcher, conflict, saved-data,
preference persistence and automatic reconnect checks. The dirty-editor warning timed out on one run;
a diagnostic rerun passed without an application change. Save/close editors before updating;
the warning is not draft recovery. These are automated checks, not user acceptance.


## v0.6.0 ? overlapping project Features

Implemented Features with names/descriptions on projects, optional multiple memberships on work items,
full-card/detail badges, and a selector on the existing board. Condensed cards remain unchanged. New
work preselects the current Feature and its project, including from the workspace-wide view. Rename
preserves membership; deleting an assigned Feature is rejected. Parent relationships and ticket IDs
are unchanged and progress counts each work item once.

Database v6 adds JSON definitions/memberships after a pre-upgrade backup. Snapshot v4 imports versions
1?3; reports include escaped Feature names/descriptions. Agent contract v5 exposes definitions,
memberships and computed names through the existing revision-checked CLI.

Validation: 110 pytest checks and Ruff passed, including migration backup/idempotence, round trips,
invalid-reference rollback, shared memberships/counting, rename, deletion safeguards and report escaping.
The dedicated Chromium workflow covered definition editing, multi-selection, both membership views,
creation preselection, rename, compact/detail presentation, external changes and filter recovery after
removal. The existing full browser suite passed all 48 themes and CRUD/export/responsive checks.
Light/dark Feature screenshots were inspected. Windows source-package checks covered launching,
restart/reconnect, saved Feature definitions, theme/border persistence and the unsaved-editor warning.
These are automated checks; user acceptance and long-term daily-use evidence remain separate.

## v0.5.0 ? field visibility, compact lanes and project-key renaming

Implemented the October 10 annotated screenshot feedback: darker field/dropdown surfaces, a persistent
1?4 px border slider in Preferences, and independently sized empty lanes with top-positioned content.
Renaming a project updates every item prefix and revision atomically, retaining UUIDs, numeric sequences,
links, tags and history. Selection follows renames made locally or through the agent interface.
Branch prefixes were explicitly deferred. Agent contract v4 documents renaming; DB v5 and snapshot v3 stay unchanged.

Validation: 96 pytest checks and Ruff passed. Chromium covered field text/label contrast in all 48 theme
variants, keyboard slider changes and persistence, UI/agent renames, empty lane geometry in both densities
and modes, and existing CRUD, drag/drop, export, responsive and conflict flows. Preferences and empty-lane
screenshots were visually inspected. This is automated evidence, not user acceptance or a full accessibility audit.
The Windows source ZIP passed launcher, conflict, saved-data/theme/border persistence, automatic reconnect
and unsaved-editor warning checks. Existing project data was not used for mutation tests.

## v0.4.0 ? focused workspace and local restart refresh

Removed Outline, Map and Dashboard, keeping the board and project overview. Main content fills the
browser width; the sidebar collapses persistently, and Home and Preferences remain in the toolbar.
Palette selection is a non-editable Preferences dropdown with source above the accepted preview;
the toolbar offers Light/Dark only. Existing links and records remain; database/API versions are unchanged.
Product scope guidance now favors a small core workflow and coherent updates without renumbering history.

Validation: 90 pytest checks and Ruff passed. Chromium exercised all 48 palette/mode combinations,
source placement, persistent non-editable selection, removed navigation, Home, keyboard sidebar collapse,
full-width layout at 2560px and mobile overflow, plus the existing CRUD, tag, export and stale-edit flows.
Preferences and collapsed-wide screenshots were inspected. This is automated evidence, not user acceptance
or a full accessibility audit.

The Windows source ZIP passed clean extraction, Start.cmd from a path with spaces, duplicate launch,
port conflict diagnostics, saved project/theme persistence, automatic refresh of an already-open browser
after restart, and a native beforeunload warning retaining an edited title when dismissed. NiceGUI supplies
the reconnect/reload; no GitHub updater or file watcher was added. Save/close forms before updating;
the warning preserves text for copying, not a draft or a usable session on the restarted server.

## v0.3.0 — project overview and simpler work cards

Implemented from October 9 feedback: project-specific overview, card-body click targets, centered
detail dialogs, footer-free cards, persistent condensed lanes, complete effort removal, and 24 palettes
with persistent searchable pickers and one live preferences preview. Database v5 and snapshot/CLI v3
remove effort, preserving old values in a pre-upgrade database backup and accepting old snapshots.

The generic startup failure was reproduced as Windows error 10048: the previous background instance
occupied the port. This is a supported explanation, not proof of the user's original underlying error.
Startup now checks the port before migration, reuses matching instances, reports other conflicts and
saves application output under the local data folder's logs directory.

Validation: 90 pytest checks passed (including all 48 light/dark token sets and migration recovery),
Ruff passed, and Chromium covered all 24 palettes in both modes, persistent picker/preview behavior,
project overview content, card-padding clicks, centered dialog geometry, condensed persistence and
keyboard opening, plus the existing CRUD, tags, exports and responsive flows. Condensed screenshot
visually inspected. New visual changes await user review; this is not a full accessibility audit.

The Windows source ZIP passed Start.cmd launch from a path with spaces, a repeated Start.ps1 launch
reusing the same workspace, a different-workspace port conflict returning a logged diagnostic without
creating its database, and full process restart with project and theme persistence.

## v0.2.0 — structured tags and theme library

Implemented: name/value tags with explicit null, inherited project defaults, per-item overrides and
copying another project's defaults. Effective tags drive cards, filtering, dashboards, detail panels,
reports and CLI output. Database version 4 creates a backup before migrating old tag arrays; snapshot
version 2 retains defaults/overrides and imports version 1. CLI contract version 2 is documented.

Five authored palette adaptations each support light/dark/system mode, with persistent selection and
an in-app swatch catalog. Original palette remains the default. No additional runtime dependencies or
external font assets were added. The original demo direction was accepted; the new individual palettes
have not yet received user acceptance.

Validation on Windows with temporary synthetic workspaces:

- 50 pytest checks passed, including migration and pre-migration backup contents, repeat initialization,
  inherited changes/null/reset semantics, strict tag validation, v1/v2 snapshots, CLI/report effective
  tags, and 4.5:1 normal-text/button token contrasts for all ten variants.
- Chromium exercised all five palettes in light/dark, reload persistence, system appearance, default-tag
  creation, null override/reset, default-set copying, external default changes, effective tag filtering,
  and the existing CRUD, revision conflict, sharing and layout flows.
- Rendered card-title contrast checked in all ten variants. Screenshots retained locally in ignored
  artifacts; Material Blue dark and Shiny Mint light visually inspected. This is not a full accessibility audit.
- New private visual-style skill structurally validated and installed separately in ai-skills; no personal
  profile or private collaboration material is included in this public application.
- Windows source ZIP passed extraction/Start.cmd checks from a path with spaces, fresh workspace
  creation, and project/mode/palette persistence through a full process restart.

The existing platform and performance limits below still apply.

## v0.1.0 release

Implemented locally: card board, hierarchy, project lifecycle, repository links, tags, effort labels,
relationship map, fixed dashboards, three theme modes, snapshot import/export, HTML reports, SQLite
backup, and a structured agent CLI. The UI refreshes external item/link changes and rejects stale edits.

Automated validation uses synthetic data only. The primary user reviewed the running demo and accepted
its visual direction for release. This does not establish long-term daily-use reliability or manual
verification of every workflow.

### Verification

- Unit/integration tests exercise hierarchy and progress, independent project lifecycle, invalid repository
  URLs, stable IDs, tag normalization, revision conflicts, import atomicity/collisions, cross-project link
  export, round trips, backups, report escaping, and the JSON agent contract.
- Chromium tests exercise light/dark/system behavior, theme persistence after reload, project/repository
  creation, task creation/editing, drag and menu status changes, stale editor rejection, external updates,
  search, all four views, diagram node clicks, project-stage filtering, snapshot/report downloads, snapshot
  import, effort preferences, and narrow viewport layout.
- Browser requests are checked for external origins. The app uses local assets in the tested flows.
- Light/dark screenshots were inspected. A Quasar color override that reduced dark-mode title readability
  was corrected. Screenshots and test databases are excluded from source control.
- Release checks: 23 data/CLI tests, Ruff, and the Chromium browser scenario.
  Sampled card-title contrast met 4.5:1 in both themes. This is not a full accessibility audit.
- The Windows source ZIP is tested with `python -m tests.release_smoke <zip>`: extraction into a path
  with spaces, the actual Start.cmd launcher, a fresh workspace, and data/theme persistence across a
  complete process restart. Release assets exclude databases and development artifacts.

### Known limits and next review

- This is a source-based browser application on loopback, not a native executable or signed installer.
- Installer size, cold-launch performance, and sustained resource use have not been benchmarked.
- Windows Chromium is tested; Firefox, Safari, macOS, Linux, screen readers, and full accessibility
  conformance are not yet verified. Visible keyboard controls and reduced-motion behavior are provided.
- Relationship maps show at most 150 matching nodes. Node arrangement is temporary. Large graphs and
  thousands of tickets have not been performance-tested.
- Dashboard charts are fixed, not a custom dashboard builder. Cross-project dependency links do not
  create schedules or automatically transition statuses. Dependency cycles are not automatically resolved.
- Project keys are immutable. Imports create copies; no concurrent-edit merge or automatic GitHub issue sync.
- Dragging changes status; within-column manual ordering is not persisted.
- Preference changes apply immediately in the current window and on other windows' next reload.
- UI and CLI errors preserve data; activity actor labels are descriptive, not authenticated identities.
- The visual direction is accepted; real daily-use feedback is the next source of product validation.

Run the checks described in the README before updating this evidence. Do not equate passing tests,
local implementation, a Git commit, a GitHub push, and a published installer.
