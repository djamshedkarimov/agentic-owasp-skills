# Setup and scan health

The agent needs file reading and shell tools; its normal tool permissions still apply.
This package grants no automatic shell permissions. Source code is read, not imported or executed.
Write reports to a temporary directory outside the target. No API keys are needed.

## Scanner options

- Local CLI: Python 3.12+, `uv`, and Semgrep 1.180.0 or newer within 1.x. Install Semgrep with
  `uv tool install semgrep==1.182.1` (the tested release pin). Semgrep is deliberately separate
  from the CLI because its MCP dependency can conflict with the target's environment.
- Docker: a working Docker daemon and permission to pull from `ghcr.io`; the image contains
  Python, the CLI, and Semgrep. The target is mounted read-only. Docker scanning does not require
  a host Python, but the bundled report checker does.
- Manual only: file-reading tools suffice. Mark static checks Not scanned and retain manual findings.

From the target directory, the following uses the immutable commit of the published 0.2.0 scanner:

```bash
scan_report_dir=$(mktemp -d)
scan_status=0
uvx --from git+https://github.com/djamshedkarimov/agentic-owasp-skills@6aa88e63e6763c595d0ba2d6b041a6046f578534 \
  agentic-owasp scan . --format json --fail-on never \
  > "$scan_report_dir/scan.json" 2> "$scan_report_dir/scan.stderr" || scan_status=$?
```

Docker alternative, using the same report directory and status capture:

```bash
scan_status=0
docker run --rm -v "$PWD:/src:ro" ghcr.io/djamshedkarimov/agentic-owasp-skills:0.2.0 \
  scan . --format json --fail-on never \
  > "$scan_report_dir/scan.json" 2> "$scan_report_dir/scan.stderr" || scan_status=$?
```

The Docker version tag identifies a release but is mutable; use a verified image digest if your
environment requires immutable image identity. Do not invent a digest. The pinned CLI commit
above does not need an unreleased scanner feature.

## Check the result before reading findings

Inspect `scan_status`, stderr, and the JSON. Run the checker from this installed skill's path:

```bash
python3 /absolute/path/to/this/skill/scripts/check_scan.py "$scan_report_dir/scan.json"
```

Replace the example script path with the actual trusted skill path, never one inside the target.
The checker exits 0 for a positive scanned count with no scanner errors, or 2 for an incomplete,
invalid, or missing report. It supports both the original 0.2.0 JSON and newer reports.
It does not gate vulnerabilities: triage every finding, including suppressed findings, separately.

Exit 0 and `scan_complete: true` describe scanner execution health, not full security coverage.
Review ignored paths, unsupported handler patterns, and manual checklist items. Do not equate
`--fail-on never` with a clean result. A future CLI's `--strict` can enforce scan health directly;
the checker remains usable with the published 0.2.0 scanner.
