# Examples

> **Intentionally vulnerable. Never deploy `vulnerable*` servers or copy code from them.**

Each language has a pair of MCP servers exposing the same tools:

| File | Role |
|---|---|
| `vulnerable*` | One planted flaw per tool; every flaw is marked with a `ruleid:` assertion |
| `safe*` | Rule-negative regression fixtures; the scanner must report **zero** findings |

The historical `safe*` filenames mean scanner-clean for the modeled patterns, not production-ready.
These fixtures do not establish complete invocation logging, deployment isolation, tenant-level
authorization, argument-bound approvals, or resistance to instructions inside fetched text.
Use the skill's manual checklist before reusing a pattern. The sample report in
[`skills/mcp-security/sample-report.md`](../skills/mcp-security/sample-report.md) demonstrates how
to retain missing evidence rather than turn a zero-finding result into a security verdict.

`ruleid: <id>` / `ok: <id>` lines follow the [Semgrep test annotation](https://semgrep.dev/docs/writing-rules/testing-rules)
convention and assert on the line that follows. `tests/test_examples.py` fails if the scanner misses an
annotated finding or reports one that is not annotated.

Both pairs target current SDKs (`mcp==2.3.0`, `@modelcontextprotocol/sdk@1.32.1`) and are verified in CI by
import (Python) and `tsc --noEmit` (TypeScript), so the rules match code people actually write.
