# Two active editions

Personal `main` and `work` are maintained in parallel. v1.0.0-work derives from personal 1.2.0 at
daf2b10. Release tags are fixed; the work branch continues. Apply shared improvements to both branches
through deliberate cherry-picks/ports and independent tests. Keep commits focused for reviewable ports.

Work-item Features remain absent from work: no definitions, memberships, filters, sorting or coloring.
Preserve work storage paths, database application_id, snapshot format, browser boundary and launchers.
Do not import personal migrations without an explicit work migration and backup tests. Never use one
edition's database with the other. Tags, hierarchy and remaining shared workflows are retained.

Analytics and work-item mapping may be future shared work; they are not part of this release.
Each release needs fresh dependency/platform evidence. Stable is a release label, not a security
certification, permanent code freeze or employer approval.
