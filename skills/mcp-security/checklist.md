# MCP Security Review Checklist

One section per control in the [crosswalk](crosswalk.md). For **Static** controls, triage the
scanner findings and spot-check what the rules can't see. For **Partial** and **Manual**
controls, answer every question from the code, config, and docs in the repo. Mark a control
**N/A** only with a stated reason (for example, stdio-only servers skip the HTTP items in 6).

## 1. Principle of least privilege

Level: Partial.

- [ ] Each upstream credential has the narrowest scope the tools need. No `*`, `admin`, `repo`, or write scopes for read-only tools.
- [ ] Each upstream service gets its own credential, not one token reused across clients.
- [ ] Short-lived or user-delegated tokens are used where the upstream supports them, instead of long-lived PATs from env.
- [ ] Tools that only read cannot reach write endpoints through the same client.

Look for: OAuth `scope=` strings, `*_TOKEN` / `*_PAT` env reads, upstream client constructors.
Pass when every credential's scope can be justified by a specific tool.

## 2. Tool description & schema integrity

Level: Static. Rule: `mcp-tool-description-injection`.

- [ ] Every tool's input schema rejects unknown fields (`additionalProperties: false`, or a strict Zod/Pydantic model).
- [ ] String parameters are bounded with `enum`, `pattern`, or `maxLength` where the domain allows.
- [ ] Tool names and descriptions are static, describe only what the tool does, and contain no instructions to the model.
- [ ] Descriptions are not built from config, network responses, or other runtime data.

Pass when the schema alone tells a client everything the tool accepts.

## 3. Sandbox and isolate servers

Level: Manual.

- [ ] The server runs as a non-root user, in a container or equivalent sandbox.
- [ ] Filesystem access is limited to declared roots; the rest of the host is not mounted.
- [ ] Outbound network access is limited to the upstreams the tools need.
- [ ] Deployment docs or manifests state these limits (Dockerfile, compose, Kubernetes `securityContext`, seccomp/AppArmor profile).

Look for: `USER`, `readOnlyRootFilesystem`, `runAsNonRoot`, volume mounts, egress policies.
N/A only if the repo ships no deployment artifacts; then say so in the report.

## 4. Human-in-the-loop for sensitive actions

Level: Manual.

- [ ] Destructive or irreversible tools (delete, send, pay, deploy, write) are identified.
- [ ] Those tools carry annotations such as `destructiveHint: true` / `readOnlyHint: false`, or require explicit confirmation (elicitation).
- [ ] Any confirmation is bound to the exact arguments that will execute, not a summary the model wrote.
- [ ] Bulk or high-impact operations have server-side limits, not only client-side prompts.

Pass when no tool can cause irreversible harm from a single model call without a human seeing the real arguments.

## 5. Input and output validation

Level: Static. Rules: `mcp-shell-injection`, `mcp-code-eval`, `mcp-sql-injection`, `mcp-path-traversal`, `mcp-ssrf`.

- [ ] Triage every finding from these rules.
- [ ] Check sinks the rules don't model: template engines, deserializers (`pickle`, `yaml.load`), ORM raw queries, `child_process` wrappers.
- [ ] Filesystem tools resolve paths and confirm they stay under an allowed root after resolution.
- [ ] Outbound URL tools allowlist hosts and block private and link-local ranges, including after redirects.

Pass when every tool argument is validated against its schema before reaching a sink.

## 6. Authentication, authorization & transport

Level: Static. Rules: `mcp-dns-rebinding`, `mcp-http-no-auth`, `mcp-token-passthrough`, `mcp-hardcoded-secret`.

- [ ] Triage every finding from these rules.
- [ ] HTTP transports validate the token's audience and issuer, not just its signature.
- [ ] Per-tool or per-resource authorization exists where users have different rights; authentication alone is not enough.
- [ ] Session IDs are random, are not used as authentication, and are bound to the user.
- [ ] TLS terminates in front of any non-localhost HTTP listener.

N/A for stdio-only servers, except `mcp-hardcoded-secret`.

## 7. Message-level integrity (optional)

Level: Manual.

- [ ] The threat model states whether messages cross an untrusted intermediary (gateway, queue, multi-hop agent).
- [ ] If they do, messages are signed or MACed and replay is prevented (nonce or timestamp).

N/A when client and server talk directly over TLS or stdio; record that as the reason.

## 8. Multi-server isolation

Level: Manual.

- [ ] The server does not read other servers' credentials, config, or state.
- [ ] Data from one user or tenant cannot appear in another's tool results or resources.
- [ ] If this is a gateway or proxy, it enforces per-server policy and does not merge tool namespaces silently.

Pass when compromising one connected server gives no access to another's data or credentials.

## 9. Supply chain security

Level: Partial.

- [ ] A lockfile is committed and CI installs from it (`uv.lock`, `poetry.lock`, `package-lock.json`, `pnpm-lock.yaml`).
- [ ] No dependency is pulled from a git URL, tarball URL, or unpinned range in production config.
- [ ] Install-time scripts (`postinstall`, custom build hooks) are absent or reviewed.
- [ ] Published artifacts (package, image) are built in CI and carry provenance.

Pass when a fresh install reproduces the reviewed dependency tree exactly.

## 10. Monitoring, logging & auditing

Level: Partial. Rule: `mcp-secret-in-log`.

- [ ] Triage every finding from the rule.
- [ ] Each tool invocation is logged with tool name, caller identity, and outcome.
- [ ] Logs omit tokens, secrets, and raw arguments that may contain PII.
- [ ] Denied and failed calls are logged as well as successful ones.

Pass when an operator could reconstruct who called which tool, when, and with what result.

## 11. Consent & installation security

Level: Manual.

- [ ] The README states every permission, credential, and network access the server needs.
- [ ] Install instructions pin a version or digest instead of `latest` or a moving branch.
- [ ] The server does not ask users to paste secrets into tool arguments.

Most of this control is client-side; review only what the server's repo controls.

## 12. Prompt injection via tool return values

Level: Partial. Rule: `mcp-raw-html-return`.

- [ ] Triage every finding from the rule.
- [ ] Tools that return third-party content (web pages, emails, tickets, files) extract the needed fields instead of returning raw text.
- [ ] Returned third-party text is bounded in size and clearly marked as untrusted data.
- [ ] No tool result can change which tools are offered or how they are described.

Pass when no attacker-controlled text reaches the model without extraction or bounds.
