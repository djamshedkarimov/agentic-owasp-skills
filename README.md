# agentic-owasp-skills

[![CI](https://github.com/djamshedkarimov/agentic-owasp-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/djamshedkarimov/agentic-owasp-skills/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/djamshedkarimov/agentic-owasp-skills/badge)](https://scorecard.dev/viewer/?uri=github.com/djamshedkarimov/agentic-owasp-skills)

Security skills and a source scanner for people **building** agentic systems, grounded in
OWASP guidance. Each skill pairs a Claude Code review workflow with deterministic
[Semgrep](https://semgrep.dev) rules that run in CI.

> **Status:** pre-release. The crosswalk, rules, CLI, Docker image, GitHub Action, and Claude Code skill are available.

## Why

Existing MCP tooling such as [Agent Scan (formerly mcp-scan)](https://github.com/invariantlabs-ai/mcp-scan)
inspects servers already **installed** on a client. Nothing checks an MCP server's **source**
against the [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)
before it ships. This project fills that gap at the author's PR, not the user's laptop.

## Skills

| Skill | Source guidance | Maps to | Version |
|---|---|---|---|
| [`mcp-security`](skills/mcp-security/) | OWASP MCP Security Cheat Sheet | MCP Top 10 (2025), Agentic Top 10 (2026) | 0.1.2 |

See the [MCP crosswalk](skills/mcp-security/crosswalk.md) for which controls are checked
automatically and which require review.

In Claude Code, install the plugin, then run `/agentic-owasp:mcp-security` from the server's
directory or ask Claude to review your MCP server:

```sh
claude plugin install agentic-owasp --marketplace 'djamshedkarimov/agentic-owasp-skills#v0.1.2'
```

The install pins the marketplace to a release tag, so it never updates on its own. To upgrade,
remove the marketplace (this also uninstalls the plugin), then run the install line again with
the new tag:

```sh
claude plugin marketplace remove agentic-owasp-skills
```

Without plugins, copy the skill directory into `~/.claude/skills/` (or a project's
`.claude/skills/`):

```sh
git clone --branch v0.1.2 https://github.com/djamshedkarimov/agentic-owasp-skills
cp -r agentic-owasp-skills/skills/mcp-security ~/.claude/skills/
```

## Usage

Two entry points share one rule set:

| Mode | For | How |
|---|---|---|
| Claude Code skill | Interactive review | Runs the scanner, then works through the manual checklist |
| CLI / GitHub Action | CI gate | Emits SARIF, fails the build at a chosen severity |

Supported targets for v1: Python (`mcp`, FastMCP) and TypeScript (`@modelcontextprotocol/sdk`).

### CLI

Requires [Semgrep](https://semgrep.dev) 1.180.0 on `PATH`. It is not a package dependency because
Semgrep pins an `mcp` version that conflicts with the servers it scans.

```sh
uv tool install semgrep==1.180.0
uvx --from git+https://github.com/djamshedkarimov/agentic-owasp-skills@v0.1.2 agentic-owasp scan path/to/server
```

| Option | Values | Default |
|---|---|---|
| `--format` | `text`, `json`, `sarif` | `text` |
| `--output` | file path | stdout |
| `--fail-on` | `error`, `warning`, `never` | `error` |

Exit codes: `0` no findings at or above `--fail-on`, `1` findings, `2` scan error.

### Docker

The image bundles the CLI and the tested Semgrep version. Mount the server source at `/src`:

```sh
docker run --rm -v "$PWD:/src:ro" ghcr.io/djamshedkarimov/agentic-owasp-skills:0.1.2 scan .
```

Release images are published for `vX.Y.Z` tags with build provenance, verifiable with
`gh attestation verify oci://ghcr.io/djamshedkarimov/agentic-owasp-skills:<version> --owner djamshedkarimov`.

### GitHub Action

```yaml
permissions:
  contents: read
  security-events: write # upload SARIF to code scanning

steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
    with:
      persist-credentials: false
  - uses: djamshedkarimov/agentic-owasp-skills@<commit-sha> # v0.1.2
    with:
      path: src
```

Pin the commit SHA of a release tag; tags can move. Findings appear as PR annotations (GitHub
shows up to 10 per severity) and, with `upload-sarif`, in full in code scanning. Runs on Linux
and macOS runners.

| Input | Values | Default |
|---|---|---|
| `path` | file or directory | `.` |
| `fail-on` | `error`, `warning`, `never` | `error` |
| `upload-sarif` | `true`, `false` (private repos without code scanning; pull requests from forks, whose token is read-only) | `true` |

The `sarif` output is the report's path.

### What the scanner does not see

The rules are tuned for few false positives, so treat findings as a floor. The skill's checklist
covers the rest.

| Not detected | Why |
|---|---|
| Tool handlers outside the known idioms: `@server.tool`, `@server.call_tool()`, `registerTool`/`tool` with an inline handler, `setRequestHandler(CallToolRequestSchema, …)`. A handler passed by name is not followed | Sources are matched by idiom |
| A tool argument that reaches a sink through a helper function | Taint is tracked within one function |
| A no-op function whose name looks like a validator, such as `validate_path` | Sanitizers are matched by name |
| Files under `test/`, `tests/`, `.claude/`, paths listed in `.gitignore` or `.semgrepignore`, files over 1 MB, files Semgrep cannot parse | Semgrep defaults; parse failures are reported as warnings |

Findings silenced with a `nosemgrep` comment are still listed, marked `suppressed`, and never fail
the gate. A scan that reaches no files warns and reports `in 0 files` rather than passing quietly.
The [threat model](docs/THREAT_MODEL.md) has the full picture.

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
zizmor, TruffleHog, dependency review, and a Grype image scan; Dependabot and OpenSSF
Scorecard run weekly.

The Grype scan fails on any high or critical finding, fixed or not. If one has no upstream
fix yet, accept that CVE alone in `.grype.yaml` with a reason, in its own PR, and remove it
once the fix ships.

## License

Code and rules: [Apache-2.0](LICENSE). Referenced OWASP material is
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and is linked, not copied.
