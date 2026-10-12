# Personal and work editions

`main` is personal Sprig; `work` is the active work edition. The work edition derives from personal
1.2.0 at daf2b10, with work-item Features removed throughout its UI, schema, CLI, sorting and reports.
Other improvements are intended for both branches after review, porting and independent tests.
Neither branch is frozen. Release tags (including v1.0.0-work) remain fixed historical deliverables.

Keep shared commits focused so they can be cherry-picked/ported. Preserve the work edition's separate
database identity, data path, snapshot format, local browser boundary and Mac/CLI packaging. Never
open either edition's database with the other or merge personal migrations into work without a plan.
Work-item Features remain personal-only. Analytics and work-item mapping are deferred future work,
not included in the current authorization/release. Security changes that apply to both should be reviewed
for both; do not merge a whole work branch back into main and accidentally remove personal capabilities.

Work release: https://github.com/Marplino-Inc/project-organize-my-shit/releases/tag/v1.0.0-work
Work branch: https://github.com/Marplino-Inc/project-organize-my-shit/tree/work
