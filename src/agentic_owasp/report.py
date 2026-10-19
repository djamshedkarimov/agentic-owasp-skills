import json
from dataclasses import asdict
from pathlib import PurePath

from agentic_owasp import __version__
from agentic_owasp.scanner import Finding, ScanResult, Severity

REPOSITORY_URL = "https://github.com/djamshedkarimov/agentic-owasp-skills"
# GitHub code scanning buckets security-severity: >= 7.0 is high, >= 4.0 is medium.
_SECURITY_SEVERITY = {Severity.ERROR: "8.0", Severity.WARNING: "5.0"}
_SARIF_LEVEL = {Severity.ERROR: "error", Severity.WARNING: "warning"}


def text(result: ScanResult) -> str:
    lines = [
        f"{f.path}:{f.line}:{f.column}: {f.severity.name.lower()} [{f.rule_id}] {f.message}" for f in result.findings
    ]
    errors = sum(f.severity is Severity.ERROR for f in result.findings)
    lines.append(f"{len(result.findings)} findings ({errors} error, {len(result.findings) - errors} warning)")
    return "\n".join(lines) + "\n"


def json_report(result: ScanResult) -> str:
    findings = [{**asdict(f), "severity": f.severity.name.lower()} for f in result.findings]
    return json.dumps({"version": __version__, "findings": findings, "errors": result.errors}, indent=2) + "\n"


def sarif(result: ScanResult) -> str:
    rules = {f.rule_id: _sarif_rule(f) for f in result.findings}
    log = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "agentic-owasp",
                        "version": __version__,
                        "informationUri": REPOSITORY_URL,
                        "rules": list(rules.values()),
                    }
                },
                "results": [_sarif_result(f) for f in result.findings],
            }
        ],
    }
    return json.dumps(log, indent=2) + "\n"


def _sarif_rule(finding: Finding) -> dict:
    metadata = finding.metadata
    return {
        "id": finding.rule_id,
        "name": finding.rule_id,
        "shortDescription": {"text": finding.rule_id},
        "fullDescription": {"text": finding.message},
        "helpUri": metadata["references"][0],
        "help": {"text": finding.message},
        "defaultConfiguration": {"level": _SARIF_LEVEL[finding.severity]},
        "properties": {
            "tags": ["security", *metadata["cwe"], *metadata["owasp-mcp"], *metadata["owasp-agentic"]],
            "precision": metadata["confidence"].lower(),
            "security-severity": _SECURITY_SEVERITY[finding.severity],
        },
    }


def _sarif_result(finding: Finding) -> dict:
    return {
        "ruleId": finding.rule_id,
        "level": _SARIF_LEVEL[finding.severity],
        "message": {"text": finding.message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": PurePath(finding.path).as_posix()},
                    "region": {
                        "startLine": finding.line,
                        "startColumn": finding.column,
                        "endLine": finding.end_line,
                        "endColumn": finding.end_column,
                    },
                }
            }
        ],
    }
