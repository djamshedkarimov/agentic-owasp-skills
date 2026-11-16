---
name: review-ai-security-slice
description: Review AI-security implementation changes or engineer feedback in this repository against scoped requirements and evidence. Use for implementation PRs and milestone readiness, not as a customer scanner or certification workflow.
---

# Review an AI-security slice

Read applicable repository instructions and [the implementation contract](../../../docs/IMPLEMENTATION_CONTRACT.md).
Apply its common requirements and relevant gates to the requested diff or feedback. Private
planning files are not prerequisites. Do not expand into unrelated repository review without cause.

- Establish base/revision, changed behavior, supported environment, and available evidence.
  Distinguish repository-confirmed defects, design omissions, unverified attack hypotheses, and
  observed target failures. Another model's agreement is not independent execution evidence.
- Trace claimed checks from requirement to procedure/implementation to evidence. Keep outcomes,
  execution state, applicability, provenance, and limitations distinct. Missing artifacts stay gaps.
- Inspect the relevant trust boundaries. Runtime and release decisions need the enforcement and
  policy contracts before dependent claims can be accepted.
- Check compatibility and installed artifacts where affected. Review instruction handling with
  hostile cases and benign documentation/fixtures. Instruction-like strings and missing annotations
  alone do not establish exploitation or missing authorization.
- Run appropriate local synthetic checks where useful. Do not execute a real target merely to test
  a hypothesis. Respect any existing declared scope, identities, destinations, and budgets.
- Report actionable findings by severity with file/line, supporting evidence, impact, and the
  smallest correction. Label proposed scenarios as untested. If no defects are found, report
  residual verification gaps; absence of findings is not proof of complete coverage.
- State which acceptance criteria are evidenced, which remain open, and the next bounded test.
  Requirements documented, implementation completed, and verification completed are separate states.

For engineer feedback, retain anonymized target/tool revisions, expected/observed behavior,
sanitized evidence, attempts/configuration, corrections, and retest results. Propose minimal
synthetic regressions for confirmed issues. Do not edit files unless fixes are requested.
