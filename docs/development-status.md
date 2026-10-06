# Development status

## v0.1 working preview

Implemented locally: card board, hierarchy, project lifecycle, repository links, tags, effort labels,
relationship map, fixed dashboards, three theme modes, snapshot import/export, HTML reports, SQLite
backup, and a structured agent CLI. The UI refreshes external item/link changes and rejects stale edits.

Validation uses synthetic data only. Automated tests are not user acceptance of the visual design.

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
- Latest local run: 18 data/CLI tests passed, Ruff passed, and the Chromium browser scenario passed.
  Sampled card-title contrast met 4.5:1 in both themes. This is not a full accessibility audit.

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
- User review of visual density, color, project stage names, and the everyday workflow is still pending.

Run the checks described in the README before updating this evidence. Do not equate passing tests,
local implementation, a Git commit, a GitHub push, and a published installer.
