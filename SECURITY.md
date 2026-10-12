# Sprig Work security scope

Purpose: single-user personal project/task tracking. No employer-system integration, credential
collection, directory crawling, keystroke capture, browser automation, AI inference or auto-update
service is part of runtime. No additional background service starts at login. The foreground Python
process runs only while launched. Game-named themes are cosmetic CSS, not games or game executables.

## Data flow and network

- Browser connects to Python on `127.0.0.1:8775`; Python reads/writes the selected SQLite file.
- CLI reads/writes the same local database through shared validation and transactions; it opens no server.
- UI changes arrive over NiceGUI WebSockets. Strict Host/Origin and cross-site checks cover HTTP and
  WebSockets; the socket origin allowlist is restricted to the bound local URL. This also resists DNS rebinding.
- CSP blocks remote images, scripts, fonts, frames and network connections from the app page. Markdown
  HTML is sanitized. Local Vue/NiceGUI still requires inline scripts/styles and eval; CSP is not a substitute
  for sanitization. No claim of a strict nonce-only CSP is made.
- External links (repository, theme provenance) can navigate externally when clicked. Setup downloads
  Python/packages using uv from its configured sources. Start.command and sprig-cli use the existing
  virtualenv directly after setup and do not run dependency installation.
- Copilot is separate software: terminal output/context may leave the device under the employer's AI
  account/settings. Sprig cannot enforce provider retention or employee data policy.

## Storage and trust boundaries

Mac default: `~/Library/Application Support/SprigWork/workspace.db`. On POSIX, launchers/use of the
store apply umask 077; newly created data directories use 0700 and existing workspace files use 0600.
Windows relies on the user's profile ACLs. Backups, exports and reports are plaintext and may contain
sensitive descriptions. Full backups include activity and undo history. SQLite is not encrypted;
use FileVault/OS account protections and approved non-synced storage. No passwords/API keys are needed.

Separate application_id, snapshot format and data path prevent accidental personal/work mixing.
Personal databases and snapshots are rejected. No personal database, exports, credentials, .venv or Git
history belongs in a release archive. Use the documented package allowlist and SHA256SUMS.

Any process/user with access to this OS account or database can inspect or modify data. Local HTTP has
no per-user login. Host/Origin checks prevent unwanted browser origins, not a malicious local process
that can forge headers. No multi-user/RBAC claims. Do not expose ports, use tunnels or host this app.
Revisions prevent accidental conflicting writes; activity labels are not authenticated or tamper-proof.
Imported text is data, not commands; repositories are links, never executed. JSON/schema validation,
SQL parameters, graph validation and atomic imports protect routine writes.

## Review evidence and remaining limits

Evidence lives in docs/security/: hash-pinned requirements, runtime dependency inventory and pip-audit
results. A point-in-time scan with no known findings is not proof of no vulnerabilities. Re-scan before
new releases. Automated tests exercise origin/host rejection, remote-content blocking, sanitization,
personal-data isolation, CLI validation, revisions, exports and UI workflows using fictional data.
The release notes record platform results. Employer endpoint configuration and actual M4 acceptance
must be checked locally. This is source packaging, not a signed/notarized Mac application.

No independent penetration test, compliance certification, legal approval or audit acceptance is claimed.
Review this document, source, dependency licenses and company rules with the appropriate owner if required.
Do not post real work data or exploit-sensitive details in public issues. Report vulnerabilities through
the repository owner's approved private channel; this package does not configure one automatically.
