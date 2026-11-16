# Repository development guidance

This repository contains an MCP source scanner and review skill. Broader AI-security modules
are planned; inspect the current implementation before describing any capability as available.

For implementation of an AI-security module, assessment contract, runtime harness, or related
MCP procedure change, use `.agents/skills/implement-ai-security-slice/SKILL.md` and read only the
applicable sections of `docs/IMPLEMENTATION_CONTRACT.md`.
For review of those changes or engineer test feedback, use
`.agents/skills/review-ai-security-slice/SKILL.md`.
These development skills are separate from the customer-facing skill under `skills/mcp-security`.

Follow CONTRIBUTING.md for code, tests, and PR conventions. Preserve existing unrelated edits.
Do not operate on the unrelated nested `agentic-owasp-skills/` checkout unless asked.
Keep private planning and real target secrets/evidence out of commits. Development must remain
reviewable from tracked requirements and PR evidence without private planning files.
