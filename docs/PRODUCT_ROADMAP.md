# OWASP skills and tools roadmap

The free MCP source-review skill is the foundation. Keep its existing code and review materials
Apache-2.0 and useful on their own. Future commercial products should earn their price through
maintained execution, integrations, evidence management, or support. Do not repackage unchanged
public instructions as an exclusive security product or imply OWASP certification.

## Coverage families

Keep mappings versioned and separate. The current skill uses the MCP Security Cheat Sheet, MCP
Top 10 (2025), and Agentic Top 10 (2026). Web and API coverage are distinct future tracks, not
synonyms for MCP coverage. Exact controls should be checked against the source before each release.

| Track | Primary guidance | Product boundary |
|---|---|---|
| MCP | https://owasp.org/www-project-mcp-top-10/ | Server source, credentials, tool schemas and transports |
| Agentic | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Tool authority, identity boundaries, untrusted context and execution |
| Web | https://owasp.org/Top10/2025/ | Application source and architecture; separate framework adapters |
| API | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ | Object/function authorization, resource limits and API inventory |

These are links to source guidance, not copied OWASP text. Mappings are project judgments.

## Proposed sequence

| Stage | Deliverable | Buyer value | Release evidence required |
|---|---|---|---|
| Free foundation | MCP review skill, report-health checker, crosswalk, setup, worked report | Useful local review with honest coverage limits | Static/unit checks, scanner fixture tests, report-health failure cases |
| First paid candidate | MCP authorization review skill plus a local evidence collector | Maps caller/tenant/tool permissions and highlights missing enforcement | Tenant-isolation and confused-deputy fixtures, actual source evidence, no credentials collected |
| Second paid candidate | Agentic tool-boundary review and regression runner | Checks exact-argument approvals, tool permissions, and untrusted context boundaries | Approved local test harness, repeatable scenarios, expected evidence and failure outcomes |
| Maintained tool candidate | CI evidence and baseline service | Tracks coverage gaps, accepted findings, changes and retests across repositories | Reproducible reports, documented retention/access, integration tests and operational support |
| Later tracks | Dedicated web or API skills | Framework-specific remediation and authorization evidence | Separate OWASP version mappings and independent benchmark repositories |

Do not implement a hosted service, process private repositories, or add recurring charges as part
of this roadmap. Define those products with actual users before building the service.

## Common output contract

Each finding should carry the target revision, source evidence, control/mapping version,
severity rationale, confidence, remediation and retest instructions. Keep automated scan health,
confirmed failures and missing manual evidence separate. Unknown is not Pass; a suppressed finding
is not automatically dismissed. Do not reduce partially reviewed controls to a coverage percentage.

## Validation before a paid release

1. Demonstrate reliable installation in a clean supported environment and at least one full report.
2. Run positive and negative fixtures plus independent real repositories with permission to review.
3. Publish benchmark revisions, expected findings, false positives/negatives and unscannable scope;
   distinguish author-written fixtures from independent evaluation.
4. Forward-test the agent workflow for missing evidence, unavailable tooling, hostile instructions,
   helper-function flows and no-op validators. Retain actual reports instead of claiming a score
   from instruction wording alone.
5. Validate the buyer's saved work/time with prospective users, then test a price. A subscription
   needs continuing maintained value and a defined update/support promise.

No paid launch, price, release date or sales forecast is committed here. The current Agensi listing
stays free; paid publishing additionally requires connected payouts.
