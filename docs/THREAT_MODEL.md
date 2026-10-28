# Threat model

What this project protects, who can attack it, and what we do about it. Dated 2026-10-28, for 0.1.1.

## What it is

A source scanner (Semgrep rules, CLI, Docker image, GitHub Action) and a Claude Code skill that
review MCP servers against the OWASP MCP Security Cheat Sheet. It reads untrusted code, never runs
it, and produces findings that gate CI or feed a review.

| Asset | Why it matters |
|---|---|
| The verdict (exit code, SARIF, report) | A wrong "clean" is worse than no scan: people stop looking |
| The scanning host | CI runner or developer laptop with its credentials |
| The release artifacts | Everyone downstream pins what we publish |

## Actors

| Actor | Position |
|---|---|
| Careless author | Writes the code being gated; wants a green check |
| Malicious contributor | Opens a PR to a repo that uses the gate; controls every file in the PR |
| Third-party server author | Publishes a server someone reviews with the skill; controls the code and its comments |
| Supply-chain attacker | Targets this repo, its dependencies, or the registry |

## Threats and controls

| # | Threat | Control | Residual risk |
|---|---|---|---|
| 1 | Author silences the gate | `nosemgrep` findings are reported as `suppressed` and annotated; a scan that reaches zero files warns and prints `in 0 files`; `.semgrepignore` and skipped directories are documented | A reviewer must read the summary line; the gate itself still passes |
| 2 | Code the rules do not see | Sources cover the decorator, inline `registerTool`/`tool`, and low-level `call_tool` / `setRequestHandler` idioms; [README](../README.md#what-the-scanner-does-not-see) lists the rest | No cross-function taint, so handlers passed by name and helper calls are unseen; sanitizers matched by name; other frameworks unseen |
| 3 | A rule regresses or misses a claimed pattern | Every rule has `ruleid`/`ok` fixtures and example servers; real-repo rescans before release; false negatives are in scope for [SECURITY.md](../SECURITY.md) | Rules are idiom-bound by design |
| 4 | Scanned code attacks the scanner | Code is parsed by Semgrep, never imported or executed; the Action runs `python -I`, resolves `semgrep` only from absolute `PATH` entries, and installs into `RUNNER_TEMP`; the image runs as non-root on a read-only mount | A Semgrep parser vulnerability; mitigated by the pinned version and Dependabot |
| 5 | Prompt injection into the skill | Scanner findings are independent of the model; the skill treats target text as data and reports reviewer-directed text as a finding | The model may still be misled on manual controls |
| 6 | Tampered dependencies or build | Hash-locked requirements, SHA-pinned actions, zizmor, dependency review, Grype gate, build provenance attestation, weekly Scorecard | The scanned image and the pushed image are separate builds from the same cache |
| 7 | Tampered repository | `main` accepts only pull requests, no force-push or deletion; CodeQL and secret scanning with push protection | Single maintainer; required status checks and tag protection are repository settings, not code |
| 8 | Bad release ships | SemVer; consumers pin the Action by commit SHA and the image by version or digest; patch release plus advisory | Registry tags cannot be withdrawn, only superseded |
| 9 | Consumer misreads results | Default gate fails on 10 of 12 rules; parse errors and empty scans are warnings in the CLI and annotations in the Action | A warning is easy to ignore |

## If it goes wrong

| Event | Response |
|---|---|
| False negative reported | Fixture first, fix the rule, patch release, advisory if a claimed pattern was missed |
| Compromised dependency | Dependabot or Grype flags it; pin out or accept per CVE in `.grype.yaml` with a reason; patch release |
| Compromised release | Consumers verify `gh attestation verify`; mark the GitHub release as pre-release, publish a fixed version, advisory |
| Semgrep behaviour changes | The CLI warns on a version mismatch; rules are tested only against the pinned version |
