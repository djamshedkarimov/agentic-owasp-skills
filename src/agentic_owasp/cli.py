import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from agentic_owasp import __version__, report
from agentic_owasp.scanner import SEMGREP_VERSION, ScanError, Severity, find_semgrep, scan, semgrep_version

EXIT_CLEAN, EXIT_FINDINGS, EXIT_ERROR = 0, 1, 2
FORMATTERS = {"text": report.text, "json": report.json_report, "sarif": report.sarif}
FAIL_ON = {"error": Severity.ERROR, "warning": Severity.WARNING, "never": None}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        installed = semgrep_version(find_semgrep())
        if installed != SEMGREP_VERSION:
            _warn(f"semgrep {installed} is installed; rules are tested against {SEMGREP_VERSION}")
        result = scan(args.path)
    except ScanError as exc:
        print(f"agentic-owasp: error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for warning in result.warnings:
        _warn(warning)
    rendered = FORMATTERS[args.format](result)
    if args.output:
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)

    threshold = FAIL_ON[args.fail_on]
    failed = threshold is not None and any(f.severity >= threshold for f in result.active)
    return EXIT_FINDINGS if failed else EXIT_CLEAN


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-owasp", description="Scan MCP server source against the OWASP MCP Security Cheat Sheet."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    scan_command = commands.add_parser("scan", help="scan a file or directory")
    scan_command.add_argument("path", nargs="?", type=Path, default=Path("."), help="target to scan (default: .)")
    scan_command.add_argument("--format", choices=FORMATTERS, default="text", help="output format (default: text)")
    scan_command.add_argument("--output", type=Path, help="write the report to a file instead of stdout")
    scan_command.add_argument(
        "--fail-on",
        choices=FAIL_ON,
        default="error",
        help="exit 1 when a finding at or above this severity is reported (default: error)",
    )
    return parser


def _warn(message: str) -> None:
    # One line per warning: a runner treats a line starting with "::" on stderr as a workflow command.
    print(f"agentic-owasp: warning: {' '.join(message.split())}", file=sys.stderr)
