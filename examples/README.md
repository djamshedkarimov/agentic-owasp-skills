# Examples

> **Intentionally vulnerable. Never deploy `vulnerable*` servers or copy code from them.**

Each language has a pair of MCP servers exposing the same tools:

| File | Role |
|---|---|
| `vulnerable*` | One planted flaw per tool; every flaw is marked with a `ruleid:` assertion |
| `safe*` | The same tools implemented correctly; the scanner must report **zero** findings |

`ruleid: <id>` / `ok: <id>` lines follow the [Semgrep test annotation](https://semgrep.dev/docs/writing-rules/testing-rules)
convention and assert on the line that follows. `tests/test_examples.py` fails if the scanner misses an
annotated finding or reports one that is not annotated.

Both pairs target current SDKs (`mcp==2.3.0`, `@modelcontextprotocol/sdk@1.32.1`) and are verified in CI by
import (Python) and `tsc --noEmit` (TypeScript), so the rules match code people actually write.
