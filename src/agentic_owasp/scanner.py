import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any

SEMGREP_VERSION = "1.179.0"
_PACKAGED_RULES = Path(__file__).parent / "rules"
_CHECKOUT_RULES = Path(__file__).resolve().parents[2] / "skills"
_NOSEM = r"nosem(?:grep)?(?::[ \t]*(?P<ids>[\w.\-]+(?:[ \t]*,[ \t]*[\w.\-]+)*))?"
_NOSEM_INLINE = re.compile(r"(?:#|//|/\*|<!--)\s*" + _NOSEM)
_NOSEM_PREVIOUS_LINE = re.compile(r"^\s*(?:#|//|/\*|<!--)\s*" + _NOSEM)


class ScanError(Exception):
    pass


class Severity(IntEnum):
    WARNING = 1
    ERROR = 2


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: str
    line: int
    column: int
    end_line: int
    end_column: int
    metadata: dict[str, Any]
    suppressed: bool


@dataclass(frozen=True)
class ScanResult:
    findings: list[Finding]
    errors: list[str]
    scanned: int

    @property
    def active(self) -> list[Finding]:
        return [f for f in self.findings if not f.suppressed]

    @property
    def suppressed(self) -> list[Finding]:
        return [f for f in self.findings if f.suppressed]

    @property
    def warnings(self) -> list[str]:
        if self.scanned:
            return self.errors
        return [*self.errors, "no Python or TypeScript files were scanned; check the target path and .semgrepignore"]


def rules_dir() -> Path:
    return _PACKAGED_RULES if _PACKAGED_RULES.is_dir() else _CHECKOUT_RULES


def find_semgrep() -> str:
    # Relative PATH entries and Windows' implicit cwd lookup would run a binary planted in the scanned repo.
    entries = os.environ.get("PATH", "").split(os.pathsep)
    search_path = os.pathsep.join(entry for entry in entries if os.path.isabs(entry))
    semgrep = shutil.which("semgrep", path=search_path)
    if not semgrep or not os.path.isabs(semgrep):
        raise ScanError(f"semgrep not found on PATH; install it with `uv tool install semgrep=={SEMGREP_VERSION}`")
    return semgrep


def semgrep_version(semgrep: str) -> str:
    return _run([semgrep, "--version", "--disable-version-check"]).strip()


def scan(target: Path) -> ScanResult:
    if not target.exists():
        raise ScanError(f"{target}: no such file or directory")
    output = _run(
        [
            find_semgrep(),
            "scan",
            "--config",
            str(rules_dir()),
            "--json",
            "--quiet",
            "--metrics=off",
            "--disable-version-check",
            # Report nosemgrep-silenced findings too; they are flagged as suppressed below.
            "--disable-nosem",
            # A project-level skill install ships the rule fixtures, which are vulnerable on purpose.
            "--exclude",
            ".claude",
            str(target),
        ]
    )
    try:
        report = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ScanError(f"semgrep returned invalid JSON: {exc}") from exc
    sources: dict[str, list[str]] = {}
    findings = []
    for result in report["results"]:
        if result["path"] not in sources:
            sources[result["path"]] = _source_lines(result["path"])
        findings.append(_finding(result, sources[result["path"]]))
    findings.sort(key=lambda f: (f.path, f.line, f.column, f.rule_id))
    errors = [error.get("message", str(error)) for error in report["errors"]]
    return ScanResult(findings, errors, len(report["paths"]["scanned"]))


def is_suppressed(source: list[str], line: int, rule_id: str) -> bool:
    """A nosemgrep comment on the finding's first line, or alone on the line above, suppresses it."""
    candidates = [(_NOSEM_INLINE, _line(source, line)), (_NOSEM_PREVIOUS_LINE, _line(source, line - 1))]
    for pattern, text in candidates:
        if match := pattern.search(text):
            ids = [rule.strip() for rule in (match["ids"] or "").split(",") if rule.strip()]
            if not ids or any(rule == rule_id or rule.endswith(f".{rule_id}") for rule in ids):
                return True
    return False


def _finding(result: dict[str, Any], source: list[str]) -> Finding:
    extra = result["extra"]
    # Semgrep prefixes IDs with the config path; the bare ID is the public, versioned name.
    rule_id = result["check_id"].rsplit(".", 1)[-1]
    line = result["start"]["line"]
    return Finding(
        rule_id=rule_id,
        severity=Severity[extra["severity"]],
        message=extra["message"],
        path=result["path"],
        line=line,
        column=result["start"]["col"],
        end_line=result["end"]["line"],
        end_column=result["end"]["col"],
        metadata=extra["metadata"],
        suppressed=is_suppressed(source, line, rule_id),
    )


def _source_lines(path: str) -> list[str]:
    try:
        return Path(path).read_text(errors="replace").splitlines()
    except OSError:
        return []


def _line(source: list[str], number: int) -> str:
    return source[number - 1] if 0 < number <= len(source) else ""


def _run(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)  # noqa: S603 - argv list, no shell
    except OSError as exc:
        raise ScanError(f"could not run semgrep: {exc}") from exc
    if completed.returncode != 0:
        raise ScanError(f"semgrep exited with {completed.returncode}: {completed.stderr.strip()}")
    return completed.stdout
