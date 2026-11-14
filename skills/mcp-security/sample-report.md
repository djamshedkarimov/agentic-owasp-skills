# Example: manual review with incomplete static coverage

This is a worked source-review example, not an executed scanner result or an independent benchmark.
Target: `examples/python/vulnerable_server.py` at upstream commit
`6aa88e63e6763c595d0ba2d6b041a6046f578534` (0.2.0). Python MCPServer; streamable HTTP;
seven registered tools. Scanner unavailable in this example, so static coverage is Not scanned.
The standalone fixture provides no production deployment or client evidence. No tool was invoked.

## Confirmed findings

| Finding | Evidence | Fix |
|---|---|---|
| Shell injection | `vulnerable_server.py:32`, tool input interpolated into `shell=True` | Use an argv list and validate the host |
| Dynamic code execution | `vulnerable_server.py:39`, `eval(expression)` | Replace expressions with typed operands and enumerated operations |
| SQL injection | `vulnerable_server.py:47`, interpolated email | Bind SQL parameters |
| Path traversal | `vulnerable_server.py:54`, uncontained filename | Resolve and enforce the workspace boundary |
| SSRF | `vulnerable_server.py:61`, arbitrary URL | Restrict scheme/hosts and handle redirects and resolved addresses |
| Tool description injection | `vulnerable_server.py:81`, requests private file access | Remove reviewer/model instructions; use static descriptions |
| Unauthenticated HTTP | `vulnerable_server.py:15,88` | Configure token verification, audience checks and authorization |
| Credential logging pattern | `vulnerable_server.py:74` | Log identifiers and outcomes, not secrets; the shown token is a dummy fixture |
| Upstream path manipulation | `vulnerable_server.py:76` | Validate the identifier and encode each URL segment |

The description at line 81 is hostile input, not an instruction to the reviewer. Severity here is
based on reachable source patterns; runtime exposure and exploitability were not exercised.

## Control evidence

| # | Control | Status | Evidence / missing evidence | Fix / next step |
|---|---|---|---|---|
| 1 | Principle of least privilege | Unknown | Fixture token at line 12 has no real scope | Obtain actual scope and upstream credential configuration |
| 2 | Tool description & schema integrity | Fail | Injected instructions at 81; unconstrained account ID at 70 | Remove instructions; bound the input schema |
| 3 | Sandbox and isolate servers | Unknown | No production runtime artifacts reviewed | Obtain runtime user, mounts, and egress policy |
| 4 | Human-in-the-loop for sensitive actions | Unknown | POST sync at 76 lacks a shown gate; impact/client behavior unknown | Establish operation impact and exact-argument approval policy |
| 5 | Input and output validation | Fail | Lines 32,39,47,54,61,76 | Validate arguments; parameterize SQL; constrain paths/URLs |
| 6 | Authentication, authorization & transport | Fail | No auth at construction 15; HTTP listener 88 | Add auth and verify deployment transport policy |
| 7 | Message-level integrity (optional) | Unknown | No intermediary threat model | Determine whether message-level integrity applies |
| 8 | Multi-server isolation | Unknown | No topology/tenant evidence | Review shared state, credentials and routing |
| 9 | Supply chain security | Unknown | Only the standalone fixture was reviewed | Inspect the target lockfiles, build and provenance |
| 10 | Monitoring, logging & auditing | Fail | Secret logging at 74; most handlers have no invocation log | Record caller/tool/outcome without secrets or raw sensitive args |
| 11 | Consent & installation security | Unknown | Client and target installation docs not reviewed | Obtain permission and installation documentation |
| 12 | Prompt injection via tool return values | Fail | Unbounded/unlabeled third-party response at 63 | Extract bounded fields and preserve trust boundaries downstream |

Static checks: Not scanned for the entire target; the Fail entries above are manual confirmations.
Relevant project crosswalk entries: MCP01/03/05/06/07/08 and ASI01/02/03/05/06/08/10.
Mappings are editorial and do not imply OWASP certification. No Pass or N/A status was inferred
from missing evidence or an unrun scanner.
