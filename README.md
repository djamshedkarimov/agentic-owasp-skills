# agentic-owasp-skills

[![CI](https://github.com/djamshedkarimov/agentic-owasp-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/djamshedkarimov/agentic-owasp-skills/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/djamshedkarimov/agentic-owasp-skills/badge)](https://scorecard.dev/viewer/?uri=github.com/djamshedkarimov/agentic-owasp-skills)

Security skills and a source scanner for people **building** agentic systems, grounded in
OWASP guidance. Each skill pairs a Claude Code review workflow with deterministic
[Semgrep](https://semgrep.dev) rules that run in CI.

> **Status:** pre-release. The crosswalk, rules, and CLI are available; the GitHub Action and Docker image are in progress.

## Why

Existing MCP tooling such as [Agent Scan (formerly mcp-scan)](https://github.com/invariantlabs-ai/mcp-scan)
inspects servers already **installed** on a client. Nothing checks an MCP server's **source**
against the [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)
before it ships. This project fills that gap at the author's PR, not the user's laptop.

## Skills

| Skill | Source guidance | Maps to | Version |
|---|---|---|---|
| [`mcp-security`](skills/mcp-security/) | OWASP MCP Security Cheat Sheet | MCP Top 10 (2025), Agentic Top 10 (2026) | unreleased |

See the [MCP crosswalk](skills/mcp-security/crosswalk.md) for which controls are checked
automatically and which require review.

## Usage

Two entry points share one rule set:

| Mode | For | How |
|---|---|---|
| Claude Code skill | Interactive review | Runs the scanner, then works through the manual checklist |
| CLI / GitHub Action | CI gate | Emits SARIF, fails the build at a chosen severity |

Supported targets for v1: Python (`mcp`, FastMCP) and TypeScript (`@modelcontextprotocol/sdk`).

### CLI

Requires [Semgrep](https://semgrep.dev) 1.179.0 on `PATH`. It is not a package dependency because
Semgrep pins an `mcp` version that conflicts with the servers it scans.

```sh
uv tool install semgrep==1.179.0
uvx --from git+https://github.com/djamshedkarimov/agentic-owasp-skills agentic-owasp scan path/to/server
```

| Option | Values | Default |
|---|---|---|
| `--format` | `text`, `json`, `sarif` | `text` |
| `--output` | file path | stdout |
| `--fail-on` | `error`, `warning`, `never` | `error` |

Exit codes: `0` no findings at or above `--fail-on`, `1` findings, `2` scan error.

## Versioning

The repo (CLI, Action, rules) follows SemVer via `vX.Y.Z` tags, with a moving `v1` tag for the
Action. Each skill also declares its own version in its `SKILL.md`. Rule changes that can
introduce new findings are a minor bump; removing or renaming a rule ID is a major bump.

## Development

```sh
make install   # uv env, pinned Semgrep, TypeScript example deps
make check     # ruff, tsc, pytest
```

## Security

Report vulnerabilities as described in [SECURITY.md](SECURITY.md). Every PR runs CodeQL,
zizmor, TruffleHog, and dependency review; Dependabot and OpenSSF Scorecard run weekly.

## License

Code and rules: [Apache-2.0](LICENSE). Referenced OWASP material is
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and is linked, not copied.
