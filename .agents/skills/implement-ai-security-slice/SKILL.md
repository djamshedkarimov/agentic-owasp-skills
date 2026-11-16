---
name: implement-ai-security-slice
description: Implement a bounded enhancement to this repository's AI-security workflows, evidence contracts, adapters, or runtime harness. Use for suite development, not customer application assessment with the existing MCP skill.
---

# Implement an AI-security slice

Read applicable repository instructions and [the implementation contract](../../../docs/IMPLEMENTATION_CONTRACT.md).
Use the common requirements and only the gates relevant to the requested change. This tracked
contract is sufficient without a private roadmap. If local planning is available, keep it private
and transfer applicable technical requirements into tracked design or the PR.

1. Inspect the working tree, relevant implementation, tests, packaging, and engineer feedback.
   Identify requested scope, current behavior, and the smallest usable result. Preserve unrelated
   edits. When preparing a PR, follow CONTRIBUTING.md without carrying unrelated branch changes.
2. State supported target/host/profile, exclusions, acceptance criteria, and prerequisites. Record
   documented, implemented, and verified states separately, with evidence or a gap. Do not describe
   planned safeguards as working controls.
3. If asked for the next slice without a named milestone, use the contract's first manual milestone.
   If target/host details are absent, prepare intake and request missing details before selecting
   target-specific checks. Continue independent preparation while waiting.
4. Implement only the authorized slice. Missing prerequisites constrain dependent work; complete
   useful procedures, fixtures, or design first. Implementation requests do not authorize real target
   execution, provider spend, publication, or protected-policy changes. Reuse session authorization
   already supplied; request only missing scope.
5. Verify applicable criteria with meaningful checks. Source review reads target files without
   importing or executing them. Separate synthetic tests from real-app observations. Tooling/access
   failures are verification gaps. Named hostile and benign cases support bounded observations only.
6. Provide an engineer test guide: supported installation, inputs/access, selected cases, expected
   observations, sanitized evidence capture, limitations, and fix/retest steps. Runtime instructions
   additionally require the contract's containment gates and a declared execution scope.
7. Report changes, checks actually run, unresolved requirements, and the next bounded step. Include
   the requirement/status/evidence record and test guide when preparing a PR. Commit, push, or
   create a PR only when requested or already authorized.

For fresh-session handoff, record slice/revision, completed work, acceptance evidence, gaps, engineer
corrections, and next action. Tracked changes must be understandable without private target evidence
or roadmap access. Do not broaden the work into the entire suite to satisfy one milestone.
