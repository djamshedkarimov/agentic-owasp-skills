# Structured intake completeness — v1

This optional preparation utility makes the pending prerequisites from the manual intake explicit.
It checks self-reported field completeness, not readiness, authorization, evidence validity, report
verdicts or target security. A human must still resolve evidence, confirm actual scope/access and
obtain engineer agreement before selecting exactly three target-specific checks. No checks or
standards are selected here. Missing target/host information still blocks that later slice.

Supported profile: a trusted copy of `tools/manual_intake_status.py`, Python 3.12+ standard library,
and an engineer-maintained private JSON sidecar to [intake.md](intake.md). A copied script works outside
the checkout without installation. This is not a plugin, scanner command or host-install acceptance.
The existing five-document bundle inventory/format stays unchanged; this optional script and guide
are not exported by that utility. Obtain them separately from the same trusted source revision.
No network, provider credentials or target access is needed to check this file. Do not import,
install, build or execute target code. The utility opens only the designated sidecar; pointers are
opaque text and are never followed. Inputs must be ordinary UTF-8 local files in a trusted working
directory, at most **1 MiB (1,048,576 bytes)** including JSON syntax and whitespace. The checker reads
at most that limit plus one detection byte and rejects oversized files before decoding or parsing.
This byte bound is not a process memory/time limit: decoded strings and parser objects add overhead.
Special files, blocking streams, adversarial filesystem mutation and resource containment are outside
this profile. Keep evidence in separate private artifacts and put only summaries/pointers here.

## Setup and fields

From the trusted checkout, create a new file outside version control:

```sh
python3 -I tools/manual_intake_status.py init /tmp/private-intake-status.json
python3 -I tools/manual_intake_status.py check /tmp/private-intake-status.json
```

The first command refuses to overwrite any existing path. The second prints JSON and exits **2**
for pending, **0** for `complete_for_human_review`, or **1** for invalid/unreadable input. Exit 0 is
only a completeness observation about supplied claims. Do not use it as a security or release gate.
Malformed or oversized documents never produce a completeness result. Diagnostics omit user-provided values and
paths; the checker does not modify the sidecar. Keep shell commands and terminal capture free of
secrets too. Use a private directory appropriate to your local access/retention rules; this utility
does not enforce file permissions or create a protected evidence store.

The root has exactly `format: "manual-intake-status-v1"` and `prerequisites`. The latter has exactly
these eight IDs, with no waiver or N/A substitute:

| ID | Intake content to supply |
|---|---|
| review_context | Assessment/date/assessor/engineer, workflow revision and baseline method/effort |
| target | One actual non-MCP target alias, source revision and artifact identity |
| host | Review product/version, OS and intended installation method |
| scope | Permitted read-only paths/artifacts, access and exclusions |
| boundaries | Actual components, identities, data/actions, flows and enforcement boundaries |
| artifacts | Available/inaccessible inventory, collector/method/date, revision/representation and alteration provenance |
| expectations | Engineer review questions and expected application behavior |
| evidence_handling | Private storage, sharing/redaction rules and retention owner |

Each entry has exactly `status` (`missing` or `supplied`), `summary` (nonempty text), `evidence` (a list
of nonempty pointer strings), `owner` and `next_action` (both nonempty text). Generated entries start
missing; replace the suggested owner with an accountable person/role privately. For missing entries,
summarize the gap and request the needed information. For supplied entries, record the actual facts
and at least one pointer into the private intake/evidence inventory, for example `E-01#scope`.
Pointers may refer to unavailable artifacts: the utility does not resolve them and cannot detect
false assertions, placeholders, conflicting facts or inaccessible evidence. Such gaps must leave the
human readiness decision pending even if the self-reported fields are complete. Retain partial
evidence and mark an entry missing whenever its prerequisite remains unresolved.

Do not copy target instructions into the status fields as review authority. Instruction-like text
is inert data to this parser; contextual classification remains a manual review task. The tool
reports only fixed prerequisite IDs, completeness and its limited basis. It does not emit Pass/Fail,
modify the three Unknown/not run/pending report slots, or infer runtime behavior.

## Engineer test and correction guide

Use disposable synthetic files and a trusted script copy outside the checkout. Record source commit,
collector/date, host/OS/Python, command, case, expected/observed exit/result, attempt, deviations and
sanitized evidence. No model is involved. Run the automated cases from the checkout:

```sh
uv run pytest tests/test_manual_intake_status.py tests/test_manual_intake_bundle.py
make check
```

| Case | Synthetic input/action | Expected observation |
|---|---|---|
| S-01 | Generate and check an untouched template | Exit 2; all eight named gaps; input unchanged |
| S-02 | Supply all entries with synthetic claims and opaque pointers | Exit 0, complete_for_human_review; evidence validity/readiness still require a human |
| S-03 | Mark scope missing again after S-02 | Exit 2, scope missing; no waiver through earlier completeness |
| H-02 | Put command-looking hostile instructions in the target summary | Inert text; no execution, scope change or security verdict; nothing from summary echoed |
| B-02 | Put a quoted attack example in a missing expectations summary | Pending remains; no failure inferred from quoted text |
| M-02 | Point supplied entries at missing artifacts | Parser does not follow pointers; human must retain evidence gaps/pending readiness |
| V-01 | Missing/extra fields, duplicate keys, malformed JSON, unsupported version/status, empty owner/action or supplied entry without a pointer | Exit 1, bounded diagnostic, no completeness result |
| P-01 | Initialize over a filled file; check a nonexistent file | Exit 1; existing bytes preserved; no private path/value in diagnostic |
| L-01 | Pad a valid pending template with whitespace to exactly 1,048,576 UTF-8 bytes, then add one byte | At limit: exit 2/pending; over limit: exit 1, no completeness result; both inputs unchanged |
| L-02 | Use multibyte summary text with fewer than 1,048,576 characters but more than that many UTF-8 bytes | Exit 1; limit counts bytes, not characters |
| L-03 | Check a disposable 64 MiB sparse file, then a small invalid UTF-8 file | Exit 1; bounded diagnostic without input values or paths; no completeness result |

Copy only the trusted Python file to a temporary directory and repeat S-01/S-02 from a different
working directory with `python3 -I` and a minimal environment. This demonstrates script portability,
not installation of the future assessment workflow. R-01 in [engineer-guide.md](engineer-guide.md)
still requires another human reviewer to resolve artifacts and reproduce reasoning; automated
schema checks cannot satisfy it. For confirmed defects, record expected/observed behavior and the
engineer correction/evidence, add a synthetic regression, retest at the corrected revision and link
the original/retest records. Keep real sidecars and evidence private.

## Requirement status and handoff

Slice: structured intake completeness v1, based on PR #67 and main `6b53dfc`. Inspected PR #67
feedback contained workflow approval only; no engineer corrections or target details. The introducing
PR supplies implementation revision and actual acceptance evidence. The cases above are expectations,
not real-target or model observations.

| Requirement | Documented | Implemented | Verification / gap |
|---|---|---|---|
| Expose pending prerequisites without selecting checks | Intake/readiness procedure; this guide | Fixed eight-entry status format, pending result | Synthetic S-01/S-03; actual intake pending |
| Distinguish completeness from evidence/readiness | This guide | Explicit self-reported basis; no pointer resolution or verdicts | S-02/M-02; human evidence review still required |
| Preserve private work and treat text as data | This guide | Exclusive creation; read-only check; fixed output IDs | P-01/H-02/B-02 regressions; no universal hostile-input claim |
| Reject malformed/incomplete schema | This guide | Strict fields/types/version and duplicate rejection | V-01 regressions; truthful contents cannot be established by schema |
| Standalone preparation utility | Setup above | Standard library script, separate from bundle/scanner packaging | Isolated copied-script regression; environments actually tested in PR |
| First installable three-check milestone | Existing manual intake/handoff | Not implemented | Target/host, agreed checks, pinned references, actual diagram, source pairs, host installation and second reviewer pending |

Next bounded action: obtain the completed intake, human evidence resolution and engineer agreement;
then implement the actual three-check source-review workflow on the declared host. Runtime harness,
importers, registries and release gates remain deferred. No real target execution or provider spend
is authorized by this preparation tool.

## Bounded-input follow-up handoff

Slice: enforce the sidecar input byte limit, based on main `15794fa` and the PR #71 handoff.
PR #71 comments/reviews contained only workflow approval; no engineer corrections or target intake.
The earlier profile required bounded files but left the bound to the caller and read the whole file.
This follow-up enforces a 1 MiB ceiling with a bounded binary read before UTF-8 decoding/JSON parsing.
The format and pending/completeness meanings are unchanged for valid UTF-8 documents within the limit.
Oversized previously accepted documents now exit 1. No new standard or target check is selected.

| Requirement | Documented | Implemented | Verification / gap |
|---|---|---|---|
| Bound the sidecar read before decoding/parsing | Profile and L-01/L-02/L-03 above | Limit plus one detection byte; oversized inputs rejected | Boundary, multibyte and sparse-file regressions; code inspection of bounded read; no measured RSS/CPU guarantee |
| Preserve status semantics and private input | Fields and original cases above | Same schema/results; no write during check; fixed diagnostic includes size guidance | Existing cases plus L-01 input-byte preservation and invalid UTF-8 regression |
| Standalone use without checkout dependencies | Setup above | Standard library only | L-01 runs a copied script with isolated Python and a minimal environment; tested host/version recorded in PR |
| First manual milestone prerequisites | Existing intake and handoff | Still pending | Actual target/host/scope/boundaries/expectations, three agreed checks, installation and second reviewer remain required |

Engineer acceptance: use a trusted script revision and disposable synthetic files outside checkout.
Run the focused pytest commands above and L-01 through L-03, recording byte counts, source revision,
OS/Python, collector, attempt, expected/observed exit and sanitized diagnostics. The automated sparse
case uses a subprocess timeout only as a regression-test guard; the utility does not enforce one.
For an oversized legitimate sidecar, preserve the original privately, move raw evidence/large text
to authorized evidence storage and retain concise summaries with opaque pointers. Recheck the smaller
copy and have a human resolve those artifacts; do not truncate JSON or interpret size rejection as
target failure. Record confirmed defects/corrections and repeat affected cases at the corrected
revision, linking original and retest evidence. No real target evidence belongs in these fixtures.

Next recommended slice remains the actual installable three-check source-review workflow after the
engineer supplies and resolves the intake prerequisites. Do not substitute further preparation
utilities for target-specific acceptance. Runtime effectiveness and human reasoning reproduction
remain unverified; no model/provider execution or spend is part of this follow-up.
