# agentic-owasp-skills

Security skills and a source scanner for people **building** agentic systems, grounded in
OWASP guidance. Each skill pairs a Claude Code review workflow with deterministic
[Semgrep](https://semgrep.dev) rules that run in CI.

> **Status:** pre-release. The crosswalk is published; rules, CLI, and GitHub Action are in progress.

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

## Versioning

The repo (CLI, Action, rules) follows SemVer via `vX.Y.Z` tags, with a moving `v1` tag for the
Action. Each skill also declares its own version in its `SKILL.md`. Rule changes that can
introduce new findings are a minor bump; removing or renaming a rule ID is a major bump.

## License

Code and rules: [Apache-2.0](LICENSE). Referenced OWASP material is
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and is linked, not copied.
