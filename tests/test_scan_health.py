import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_owasp import report
from agentic_owasp.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, main
from agentic_owasp.scanner import Finding, ScanResult, Severity

SKILL_DIR = Path(__file__).resolve().parents[1] / "skills" / "mcp-security"
SPEC = importlib.util.spec_from_file_location("check_scan", SKILL_DIR / "scripts" / "check_scan.py")
assert SPEC and SPEC.loader
health = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(health)


class ScanHealthTests(unittest.TestCase):
    def invoke(self, result: ScanResult, strict: bool = True) -> tuple[int, dict, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            patch("agentic_owasp.cli.find_semgrep", return_value="/trusted/semgrep"),
            patch("agentic_owasp.cli.semgrep_version", return_value="1.182.1"),
            patch("agentic_owasp.cli.scan", return_value=result),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            args = ["scan", ".", "--format", "json", "--fail-on", "never"]
            if strict:
                args.append("--strict")
            code = main(args)
        return code, json.loads(out.getvalue()), err.getvalue()

    def test_empty_scan_is_error_even_with_fail_on_never(self) -> None:
        code, payload, err = self.invoke(ScanResult([], [], 0))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIs(payload["scan_complete"], False)
        self.assertTrue(payload["warnings"])
        self.assertIn("no Python or TypeScript files were scanned", err)

    def test_partial_parse_error_is_error(self) -> None:
        code, payload, _ = self.invoke(ScanResult([], ["Syntax error in server.py"], 1))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(payload["errors"], ["Syntax error in server.py"])

    def test_legacy_gate_stays_permissive_but_reports_incomplete(self) -> None:
        for result in [ScanResult([], [], 0), ScanResult([], ["parse error"], 1)]:
            with self.subTest(result=result):
                code, payload, _ = self.invoke(result, strict=False)
                self.assertEqual(code, EXIT_CLEAN)
                self.assertIs(payload["scan_complete"], False)

    def test_complete_scan_stays_successful(self) -> None:
        code, payload, _ = self.invoke(ScanResult([], [], 1))
        self.assertEqual(code, EXIT_CLEAN)
        self.assertIs(payload["scan_complete"], True)
        self.assertEqual(payload["warnings"], [])

    def test_incomplete_scan_preserves_findings(self) -> None:
        finding = Finding("mcp-code-eval", Severity.ERROR, "eval", "server.py", 1, 1, 1, 9, {}, False)
        code, payload, _ = self.invoke(ScanResult([finding], ["another file could not parse"], 2))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(payload["findings"][0]["rule_id"], "mcp-code-eval")

    def test_healthy_scan_still_fails_vulnerability_threshold(self) -> None:
        finding = Finding("mcp-code-eval", Severity.ERROR, "eval", "server.py", 1, 1, 1, 9, {}, False)
        with (
            patch("agentic_owasp.cli.find_semgrep", return_value="/trusted/semgrep"),
            patch("agentic_owasp.cli.semgrep_version", return_value="1.182.1"),
            patch("agentic_owasp.cli.scan", return_value=ScanResult([finding], [], 1)),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(main(["scan", ".", "--strict"]), EXIT_FINDINGS)

    def test_incomplete_report_is_written_before_exit(self) -> None:
        with (
            tempfile.TemporaryDirectory() as folder,
            patch("agentic_owasp.cli.find_semgrep", return_value="/trusted/semgrep"),
            patch("agentic_owasp.cli.semgrep_version", return_value="1.182.1"),
            patch("agentic_owasp.cli.scan", return_value=ScanResult([], [], 0)),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            path = Path(folder) / "scan.json"
            args = ["scan", ".", "--strict", "--format", "json", "--output", str(path)]
            self.assertEqual(main(args), EXIT_ERROR)
            self.assertIs(json.loads(path.read_text())["scan_complete"], False)

    def test_sarif_marks_incomplete_execution(self) -> None:
        for result in [ScanResult([], [], 0), ScanResult([], ["parse error"], 1)]:
            with self.subTest(result=result):
                invocation = json.loads(report.sarif(result))["runs"][0]["invocations"][0]
                self.assertIs(invocation["executionSuccessful"], False)
                self.assertTrue(invocation["toolExecutionNotifications"])

    def test_text_marks_incomplete_execution(self) -> None:
        self.assertIn("scan incomplete", report.text(ScanResult([], [], 0)))

    def test_checker_accepts_published_020_and_current_reports(self) -> None:
        self.assertEqual(health.problems({"scanned": 1, "findings": [], "errors": []}), [])
        self.assertEqual(health.problems(json.loads(report.json_report(ScanResult([], [], 1)))), [])

    def test_checker_rejects_zero_files_and_parse_errors(self) -> None:
        for result in [ScanResult([], [], 0), ScanResult([], ["parse error"], 1)]:
            with self.subTest(result=result):
                self.assertTrue(health.problems(json.loads(report.json_report(result))))

    def test_checker_rejects_invalid_schema(self) -> None:
        for payload in [None, [], {}, {"scanned": True}, {"scanned": -1}, {"scanned": "1"}]:
            with self.subTest(payload=payload):
                self.assertTrue(health.problems(payload))

    def test_checker_respects_explicit_incomplete_flag(self) -> None:
        payload = {"scanned": 1, "findings": [], "errors": [], "scan_complete": False}
        self.assertEqual(health.problems(payload), ["Scanner marked the scan incomplete"])

    def test_checker_separates_health_from_vulnerabilities(self) -> None:
        payload = {"scanned": 1, "findings": [{"suppressed": True}], "errors": []}
        self.assertEqual(health.problems(payload), [])

    def test_checker_cli_good_bad_and_missing_reports(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scan.json"
            for contents, expected in [
                ("{", EXIT_ERROR),
                (json.dumps({"scanned": 1, "findings": [], "errors": []}), EXIT_CLEAN),
            ]:
                with self.subTest(contents=contents), contextlib.redirect_stdout(io.StringIO()) as out:
                    path.write_text(contents)
                    self.assertEqual(health.main([str(path)]), expected)
                    self.assertIs(json.loads(out.getvalue())["scan_complete"], expected == EXIT_CLEAN)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(health.main([str(Path(folder) / "missing.json")]), EXIT_ERROR)
