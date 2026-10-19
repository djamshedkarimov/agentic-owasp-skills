# Security Policy

## Reporting a vulnerability

Report vulnerabilities privately through [GitHub Security Advisories](https://github.com/djamshedkarimov/agentic-owasp-skills/security/advisories/new). Do not open a public issue.

Expect an acknowledgement within 5 business days. Fixes are released as a new patch version and the advisory is published once a fix is available.

## Scope

| In scope | Out of scope |
|---|---|
| Scanner code, rules, GitHub Action, Docker image | Findings in `examples/**/vulnerable*` and rule test fixtures, which are deliberately vulnerable |
| A rule that misses a pattern it claims to detect (false negative) | False positives; open a regular issue |
