# AI-security implementation contract

This contract guides development of this repository. Requirements below are not claims that the
planned modules or safeguards exist. Apply only the sections relevant to the current change.
The public product roadmap describes direction; this document defines reviewable technical gates.

## Common requirements

- Deliver one bounded, usable slice with supported inputs, environment, exclusions, and acceptance
  criteria. Preserve existing unrelated edits and scanner contracts. Follow CONTRIBUTING.md.
- Record requirements in tracked design or the PR. For each, distinguish **documented**,
  **implemented**, and **verified**; include evidence or an unresolved gap. A safeguard can be
  implemented but unverified. Keep sensitive target material and commercial planning private.
- Pin the exact source/version of selected standards during implementation. Use original procedures
  and attribution. Risk-category mappings are editorial judgments, not exhaustive verification or
  certification. Implement selected checks rather than the whole standards catalog.
- Separate control outcomes (Pass, Fail, Unknown, N/A) from execution (completed, not run,
  unsupported, error). N/A needs a reason; absent required evidence yields Unknown. Preserve legacy
  Not scanned semantics and scan health. One passing check cannot pass unchecked requirements.
- Record artifact identity, revision, collector/method, alteration permissions, evidence pointers,
  configuration, attempts, limitations, and retest links as applicable. Distinguish target assertions,
  assessor observations, and independently corroborated effects. Hashes bind bytes, not execution.
- Treat target instructions as untrusted evidence. Classify contextually as benign documentation or
  fixture, injection attempt, or confirmed requirement failure. Do not infer exploitation merely
  from instruction-like text. Extraction, labels, and size limits alone do not establish resistance.
- Verify named hostile cases and benign negative cases under recorded host/model settings. Record
  corpus, expected behavior, attempts, deviations, and uncertainty; avoid universal resistance claims.
- Provide an engineer test guide and sanitized report. Record expected/observed behavior, target/tool
  revision, feedback, and fix/retest results. Turn meaningful confirmed issues into synthetic regressions.

A useful PR record is:

| Requirement | Documented reference | Implementation reference/status | Verification evidence/status | Gap / next step |
|---|---|---|---|---|
| Selected acceptance criterion | Tracked design or PR text | Changed code/procedure or pending | Actual check, conditions and result or unverified | Missing evidence or follow-up |

## MCP procedure changes

Before completing a procedure patch:

- Keep authorization review applicable across transports. Stdio exempts only justified HTTP-specific
  items; review local caller permissions, upstream authority, inherited credentials, and tenant scope.
- Where message replay protection applies, require authenticated identifiers/payload bindings,
  atomic duplicate rejection, validity windows, shared state across accepting instances where needed,
  and review of concurrency, expiry, restart, and store failure. A timestamp alone is insufficient.
- Review complete tool definitions: inputSchema, outputSchema, annotations, names, and descriptions.
  Record the reviewed representation and digest and require review on change. Metadata integrity
  does not establish effective server behavior; absent runtime evidence stays Unknown.
- Separate input validation from output-consumer safety. Trace tool/model outputs to HTML/Markdown,
  SQL, shell, templates, and privileged calls; require destination-specific controls. Input schemas
  cannot pass output handling. Missing consumer visibility is an evidence gap.
- Align README, crosswalk, checklist, and diagnostics around selected automated patterns plus manual
  verification. Missing annotations do not prove missing approvals. Follow the actual authorization
  and argument-bound approval gate. No measured false-positive claim without representative data.

Acceptance evidence: consistent procedures/diagnostics and examples separating input validation,
output safety, definition integrity, and behavior, including benign instruction-like negative cases.

## First manual milestone

Build one installable manual workflow for one non-MCP application and exactly three checks selected
from the engineer's actual target. Prepare intake if target or host information is missing. Example
candidate areas are identity-to-data authorization, untrusted content reaching privileged consumers,
and request/cost limits; select based on the application rather than assuming applicability.

Deliver scope/intake, one trust-boundary diagram, pinned references, original procedures, sanitized
report, and known-defect/corrected source fixtures. Defer runtime harness, scanner importer,
portfolio-wide registry, and consolidated release gate.

Acceptance:

1. Install the packaged artifact on one declared host outside the checkout without checkout-only
   dependencies. Resolve all applicable plugin metadata references inside that artifact. Inspect the
   current icon path/content mismatch; use the supported host's format, not renamed file bytes.
2. All three checks record outcome, execution, applicability, resolvable evidence or a named gap,
   rationale, limitations, and next verification step.
3. A second reviewer resolves the artifacts and reproduces the reasoning. This is distinct from
   independent-user acceptance of a future runtime harness.
4. Named hostile and benign cases preserve intended scope/verdict rules under recorded conditions;
   record deviations and limitations, with no universal claim. Missing artifacts produce Unknown.
5. Known-defect/corrected pairs yield predefined source-review conclusions. Runtime effectiveness
   remains unverified. Record engineer corrections and the next bounded verification step.

## Structured evidence, shared components, and compatibility

Before dependent adapter work:

- Specify collection trust and bindings. Older scanner reports lack target digests/file inventories
  and runtime identity; preserve unknown provenance. Collect new bindings through a trusted wrapper
  at collection time rather than reconstructing facts the original report never recorded.
- Establish explicit rule selection before adding modules: current discovery and wheel packaging
  traverse skill rule directories and could silently expand existing scans.
- Specify shared dependency/version resolution for wheels and standalone skills. Check actual package
  contents and references after installation outside the checkout.
- Maintain an affected compatibility matrix: scanner 0.2.0/0.2.1 imports, suppressed findings,
  strict/permissive exits, SARIF health, stable rule IDs, CLI/Action behavior, standalone installation,
  and declared OS/Python/Semgrep combinations. Nonblocking latest-version CI is not future assurance.

Acceptance evidence: meaningful import/compatibility cases, installed-artifact checks, and explicit
untested combinations. Do not change legacy CLI/output behavior merely to introduce a new contract.

## Runtime enforcement

Before implementing a target runtime adapter, define and verify one supported environment:

- A runtime threat model separate from the source scanner's no-target-execution model. Diagram the
  assessor host, trusted orchestrator/enforcer, target, observer, credentials, provider, and evidence
  store. Identify who can modify each interface; enforcement is independent of target and model.
- Enforced mounts/paths, inherited credentials/environment, network destinations including redirects
  and DNS changes, provider access, process-tree termination, and cleanup after failures. Document
  a security basis for the selected environment; a container alone is not containment evidence.
- Atomic concurrent budgets for actions, time, resources and provider spend, including delayed or
  missing usage accounting. Unsupported hard limits must not be advertised as enforced.
- Escape-attempt fixtures for prohibited paths/credentials/egress, redirects/DNS, parallel overruns,
  orphan processes, observer failure, and failed cleanup, with observed enforcement evidence.

Real target execution additionally requires declared scope, permitted actions, destinations,
identities/data, and budgets. Existing authorization persists; request only missing scope. A source
review never executes the target. Distinguish harness errors from target failures and observe actual
calls/effects. Model-dependent scenarios record corpus, settings, repetitions, and uncertainty.

Acceptance evidence: predefined planted failures and corrections plus containment cases demonstrating
blocked actions under stated conditions. Unknown enforcement cannot be promoted to a safety claim.

## Module-specific prerequisites

- **Agents:** support one direct function/API adapter without requiring MCP. Define caller/tool/resource
  authority, identity propagation, argument-bound approvals, replay/expiry, delegation, and shared
  budgets. Verify actual calls and effects, not agent summaries.
- **RAG/memory:** obtain an engineer-approved principal/resource/action oracle. Observe authorization
  before model access. Name indexes, derived data, caches, and memory paths covered. Define revocation
  and deletion deadlines, start events and completion observations. Two tenants/roles alone are not
  coverage; separate retrieval-policy failures from stochastic disclosure.
- **Deployment:** one profile first, read-only collection by default; distinguish desired configuration
  from observed runtime. Each planted defect has a predefined failure and a correction changes only
  expected outcomes. Source review cannot establish runtime isolation.
- **Supply chain:** inspect origins/digests/provenance/loading settings without loading untrusted models
  on the assessor host. Use isolated tamper fixtures. Hosted internals may be Unknown; do not claim
  training-data integrity or adversarial robustness from provider names or responses.

## Consolidated review and CI policy

Before accepting release gates:

- Define protected policy ownership and authorized changes independently of contributor-controlled
  scope, baselines, reports, N/A decisions, and acceptance files. Specify N/A/exception approval,
  expiry, and audit trail. Risk acceptance retains the observed failure.
- Missing/invalid/unavailable/unauthorized policy cannot produce a passing gate. Separate execution
  health, security outcomes, exceptions, and human release decisions.
- Define explicit input/dependency freshness rules with mutation fixtures. Unknown change impact
  makes evidence stale. Retain conflicts and gaps when consolidating; incomplete required checks
  cannot silently pass.
- Process untrusted reports/artifacts as data. Privileged CI must not execute their contents or run
  contributor-controlled checkout code with privileged credentials.

Acceptance evidence: planted regressions, stale/conflicting evidence, unauthorized policy changes,
expired exceptions, scope reduction, and policy-load failures produce predefined gate outcomes.
