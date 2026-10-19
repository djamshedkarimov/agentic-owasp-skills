# MCP Security Crosswalk

Maps each control in the [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)
to the [OWASP MCP Top 10 (2025)](https://owasp.org/www-project-mcp-top-10/) and the
[OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/),
and states how this project verifies it.

> The ID mappings are this project's editorial judgment. OWASP does not publish an official
> crosswalk between these three documents. Sources retrieved 2026-10-16.

## Detection levels

| Level | Meaning |
|---|---|
| **Static** | Detectable from server source by the scanner with low false-positive rate |
| **Partial** | Scanner flags common anti-patterns; a reviewer must confirm the control as a whole |
| **Manual** | Depends on runtime, deployment, or client UX; covered by the skill's review checklist only |

## Controls

| # | Cheat sheet control | MCP Top 10 | Agentic Top 10 | Level | What is checked | Rules |
|---|---|---|---|---|---|---|
| 1 | Principle of least privilege | MCP01, MCP02 | ASI03 | Partial | Wildcard or write-level OAuth scopes; one credential reused across upstream clients; long-lived PATs loaded from env | — |
| 2 | Tool description & schema integrity | MCP03 | ASI01, ASI02 | Static | `inputSchema` without `additionalProperties: false`; unconstrained string params (no `pattern`/`enum`/`maxLength`); instruction-like text in tool descriptions | — |
| 3 | Sandbox and isolate servers | MCP05 | ASI05 | Manual | Container/seccomp profile, filesystem and network scope | — |
| 4 | Human-in-the-loop for sensitive actions | — | ASI02, ASI09 | Manual | Destructive tools marked and gated; approvals bound to exact arguments | — |
| 5 | Input and output validation | MCP05, MCP06 | ASI02, ASI05 | Static | Tool args reaching shell exec, `eval`, SQL string building, filesystem paths, or outbound URLs without validation | `mcp-shell-injection`, `mcp-code-eval`, `mcp-sql-injection`, `mcp-path-traversal`, `mcp-ssrf` |
| 6 | Authentication, authorization & transport | MCP01, MCP07 | ASI03 | Static | HTTP transport without auth middleware; bind to `0.0.0.0`; missing `Origin`/`Host` validation; no token audience check; inbound MCP token forwarded upstream; hardcoded secrets | `mcp-dns-rebinding`, `mcp-http-no-auth`, `mcp-token-passthrough`, `mcp-hardcoded-secret` |
| 7 | Message-level integrity (optional) | MCP07 | ASI07 | Manual | Only where the threat model requires it | — |
| 8 | Multi-server isolation | MCP03, MCP10 | ASI06 | Manual | Shared credentials or context across servers; gateway policy | — |
| 9 | Supply chain security | MCP03, MCP04 | ASI04 | Partial | Missing lockfile; unpinned or git-URL dependencies; install-time scripts | — |
| 10 | Monitoring, logging & auditing | MCP01, MCP08 | ASI03, ASI08, ASI10 | Partial | Tool handlers with no invocation logging; secrets or tokens passed to loggers | `mcp-secret-in-log` |
| 11 | Consent & installation security | MCP04, MCP09 | ASI04, ASI09 | Manual | Client-side behavior; out of scope for server source | — |
| 12 | Prompt injection via tool return values | MCP06 | ASI01, ASI06 | Partial | Raw HTML or unbounded third-party text returned from tools without extraction | — |

## Coverage by Top 10 entry

| ID | Title | Controls |
|---|---|---|
| MCP01 | Token Mismanagement & Secret Exposure | 1, 6, 10 |
| MCP02 | Privilege Escalation via Scope Creep | 1 |
| MCP03 | Tool Poisoning | 2, 8, 9 |
| MCP04 | Software Supply Chain Attacks & Dependency Tampering | 9, 11 |
| MCP05 | Command Injection & Execution | 3, 5 |
| MCP06 | Prompt Injection via Contextual Payloads | 5, 12 |
| MCP07 | Insufficient Authentication & Authorization | 6, 7 |
| MCP08 | Lack of Audit and Telemetry | 10 |
| MCP09 | Shadow MCP Servers | 11 |
| MCP10 | Context Injection & Over-Sharing | 8 |
| ASI01 | Agent Goal Hijack | 2, 12 |
| ASI02 | Tool Misuse & Exploitation | 2, 4, 5 |
| ASI03 | Identity & Privilege Abuse | 1, 6, 10 |
| ASI04 | Agentic Supply Chain Vulnerabilities | 9, 11 |
| ASI05 | Unexpected Code Execution (RCE) | 3, 5 |
| ASI06 | Memory & Context Poisoning | 8, 12 |
| ASI07 | Insecure Inter-Agent Communication | 7 |
| ASI08 | Cascading Failures | 10 |
| ASI09 | Human-Agent Trust Exploitation | 4, 11 |
| ASI10 | Rogue Agents | 10 |
