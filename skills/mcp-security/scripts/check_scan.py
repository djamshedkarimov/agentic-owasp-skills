"""Check scanner execution health without importing or executing the reviewed target."""

import argparse
import json
from pathlib import Path


def problems(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["Report must be a JSON object"]
    scanned = payload.get("scanned")
    findings, errors = payload.get("findings"), payload.get("errors")
    if type(scanned) is not int or scanned < 0 or not isinstance(findings, list) or not isinstance(errors, list):
        return ["Report needs a nonnegative integer scanned count and findings/errors arrays"]
    issues = []
    if not scanned:
        issues.append("No files were scanned")
    if errors:
        issues.append("Scanner reported errors")
    if "scan_complete" in payload and payload["scan_complete"] is not True:
        issues.append("Scanner marked the scan incomplete")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="agentic-owasp JSON report")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.report.read_text())
        issues = problems(payload)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues = [f"Could not read scanner report: {exc}"]
    print(json.dumps({"scan_complete": not issues, "problems": issues}))
    return 2 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
