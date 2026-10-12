# Security evidence - 2026-10-12

Runtime requirements exported with uv 0.11.6 from uv.lock, without development dependencies.
Auditor: pip-audit 2.10.1. JSON report and CycloneDX SBOM contain package names/versions only,
not workspace content. Scan command:

```
uvx pip-audit -r requirements.txt --no-deps --disable-pip --format json --output docs/security/dependency-audit.json
```

Result: no known vulnerabilities reported for the requirements applicable to the scanning Windows
Python 3.12 environment. This is point-in-time evidence, not absence-of-vulnerabilities proof.
macOS CI repeats an audit on its resolved environment. Dependency inventory includes package license
metadata; verify original distribution licenses if redistributing dependencies. The source release
bundles no dependency binaries. The project has no general open-source LICENSE grant; use is being
prepared for the repository owner's personal productivity purpose. Third-party licenses are unchanged.

Source and security checks: Host/Origin rejection, cross-site WebSocket rejection, CSP network limits,
sanitation, separate data format, revision conflicts and local-only operation are covered by tests.
The package allowlist excludes private workspaces and Git history. SHA256SUMS verifies archive integrity,
not publisher identity. No notarization, code-signing or independent security audit is claimed.

References: https://github.com/zauberzeug/nicegui/security/advisories
https://docs.astral.sh/uv/reference/policies/platforms/
