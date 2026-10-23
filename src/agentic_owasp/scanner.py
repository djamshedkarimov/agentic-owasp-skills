import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any

SEMGREP_VERSION = "1.179.0"
_PACKAGED_RULES = Path(__file__).parent / "rules"
_CHECKOUT_RULES = Path(__file__).resolve().parents[2] / "skills"


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
            # Keep findings silenced by nosemgrep comments in the output, flagged, so suppressions stay visible.
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
    findings = sorted(map(_finding, report["results"]), key=lambda f: (f.path, f.line, f.column, f.rule_id))
    errors = [error.get("message", str(error)) for error in report["errors"]]
    return ScanResult(findings, errors, len(report["paths"]["scanned"]))


def _finding(result: dict[str, Any]) -> Finding:
    extra = result["extra"]
    return Finding(
        # Semgrep prefixes IDs with the config path; the bare ID is the public, versioned name.
        rule_id=result["check_id"].rsplit(".", 1)[-1],
        severity=Severity[extra["severity"]],
        message=extra["message"],
        path=result["path"],
        line=result["start"]["line"],
        column=result["start"]["col"],
        end_line=result["end"]["line"],
        end_column=result["end"]["col"],
        metadata=extra["metadata"],
        suppressed=extra.get("is_ignored", False),
    )


def _run(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)  # noqa: S603 - argv list, no shell
    except OSError as exc:
        raise ScanError(f"could not run semgrep: {exc}") from exc
    if completed.returncode != 0:
        raise ScanError(f"semgrep exited with {completed.returncode}: {completed.stderr.strip()}")
    return completed.stdout
