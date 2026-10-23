import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
from catalog import REPO_ROOT, load_rules

from agentic_owasp.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, main
from agentic_owasp.scanner import find_semgrep

EXAMPLES = REPO_ROOT / "examples"
SAFE_SERVERS = [EXAMPLES / "python" / "safe_server.py", EXAMPLES / "typescript" / "safe-server.ts"]
WARNING_ONLY_SERVER = """\
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo", host="0.0.0.0")
"""
UNAUTHENTICATED_HTTP_SERVER = """\
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")
mcp.run(transport="streamable-http")
"""


def _scan(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str]:
    code = main(["scan", *args])
    return code, capsys.readouterr().out


def test_every_rule_fires_on_the_vulnerable_examples(capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _scan(capsys, str(EXAMPLES), "--format", "json")
    assert code == EXIT_FINDINGS
    assert {f["rule_id"] for f in json.loads(out)["findings"]} == {rule.id for rule in load_rules()}


@pytest.mark.parametrize("server", SAFE_SERVERS, ids=lambda path: path.name)
def test_safe_examples_pass_the_strictest_gate(server: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _scan(capsys, str(server), "--fail-on", "warning")
    assert code == EXIT_CLEAN
    assert out.endswith("0 findings (0 error, 0 warning) in 1 files\n")


@pytest.mark.parametrize(
    ("fail_on", "expected"), [("never", EXIT_CLEAN), ("error", EXIT_CLEAN), ("warning", EXIT_FINDINGS)]
)
def test_fail_on_threshold(fail_on: str, expected: int, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    server = tmp_path / "server.py"
    server.write_text(WARNING_ONLY_SERVER)
    code, out = _scan(capsys, str(server), "--fail-on", fail_on)
    assert code == expected
    assert "warning [mcp-dns-rebinding]" in out


def test_default_gate_fails_an_unauthenticated_http_server(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    server = tmp_path / "server.py"
    server.write_text(UNAUTHENTICATED_HTTP_SERVER)
    code, out = _scan(capsys, str(server))
    assert code == EXIT_FINDINGS
    assert "error [mcp-http-no-auth]" in out


def test_nosemgrep_suppressions_are_reported_but_do_not_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    server = tmp_path / "server.py"
    server.write_text(UNAUTHENTICATED_HTTP_SERVER.replace("\n", "  # nosemgrep\n"))
    code, out = _scan(capsys, str(server), "--format", "json")
    assert code == EXIT_CLEAN
    (finding,) = json.loads(out)["findings"]
    assert finding["rule_id"] == "mcp-http-no-auth"
    assert finding["suppressed"] is True
    code, out = _scan(capsys, str(server))
    assert code == EXIT_CLEAN
    assert "suppressed [mcp-http-no-auth]" in out
    assert out.endswith("0 findings (0 error, 0 warning) in 1 files, 1 suppressed by nosemgrep\n")


def test_scanning_no_files_warns_instead_of_passing_silently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "server.py").write_text(UNAUTHENTICATED_HTTP_SERVER)
    (tmp_path / ".semgrepignore").write_text("*\n")
    code = main(["scan", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == EXIT_CLEAN
    assert captured.out == "0 findings (0 error, 0 warning) in 0 files\n"
    assert "no Python or TypeScript files were scanned" in captured.err


def test_claude_directory_is_not_scanned(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    installed_skill = tmp_path / ".claude" / "skills" / "mcp-security"
    installed_skill.mkdir(parents=True)
    (installed_skill / "server.py").write_text(UNAUTHENTICATED_HTTP_SERVER)
    (tmp_path / "server.py").write_text(UNAUTHENTICATED_HTTP_SERVER)
    code, out = _scan(capsys, str(tmp_path), "--format", "json")
    assert code == EXIT_FINDINGS
    assert {Path(f["path"]).parent for f in json.loads(out)["findings"]} == {tmp_path}


def test_sarif_report_is_well_formed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "report.sarif"
    target = EXAMPLES / "python" / "vulnerable_server.py"
    code, out = _scan(capsys, str(target), "--format", "sarif", "--output", str(output))
    assert code == EXIT_FINDINGS
    assert out == ""
    log = json.loads(output.read_text())
    assert log["version"] == "2.1.0"
    (run,) = log["runs"]
    rules = {rule["id"]: rule for rule in run["tool"]["driver"]["rules"]}
    assert run["results"]
    for result in run["results"]:
        rule = rules[result["ruleId"]]
        assert result["level"] == rule["defaultConfiguration"]["level"]
        assert float(rule["properties"]["security-severity"]) >= 4.0
        assert any(tag.startswith("MCP") for tag in rule["properties"]["tags"])
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] >= 1
    (invocation,) = run["invocations"]
    assert invocation["executionSuccessful"] is True
    assert invocation["toolExecutionNotifications"] == []


def test_sarif_carries_suppressions_and_warnings_as_notifications(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "server.py").write_text(UNAUTHENTICATED_HTTP_SERVER.replace("\n", "  # nosemgrep\n"))
    (tmp_path / "broken.py").write_text("def (:\n")
    output = tmp_path / "report.sarif"
    assert _scan(capsys, str(tmp_path), "--format", "sarif", "--output", str(output))[0] == EXIT_CLEAN
    (run,) = json.loads(output.read_text())["runs"]
    assert run["results"] == []
    notifications = run["invocations"][0]["toolExecutionNotifications"]
    assert [n["level"] for n in notifications] == ["warning", "note"]
    assert "broken.py" in notifications[0]["message"]["text"]
    assert notifications[1]["descriptor"] == {"id": "mcp-http-no-auth"}
    assert notifications[1]["locations"][0]["physicalLocation"]["region"]["startLine"] == 4


def test_missing_target_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scan", "does-not-exist"]) == EXIT_ERROR
    assert "no such file or directory" in capsys.readouterr().err


def test_missing_semgrep_is_an_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PATH", "")
    assert main(["scan", str(EXAMPLES)]) == EXIT_ERROR
    assert "semgrep not found" in capsys.readouterr().err


def test_semgrep_is_not_resolved_from_relative_path_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    planted = tmp_path / "semgrep"
    planted.write_text("#!/bin/sh\nexit 0\n")
    planted.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", f".{os.pathsep}{os.environ['PATH']}")
    assert Path(find_semgrep()) != planted


def test_wheel_ships_rules_without_test_files(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv, "uv not on PATH"
    subprocess.run([uv, "build", "--wheel", "--quiet", "--out-dir", str(tmp_path)], cwd=REPO_ROOT, check=True)
    (wheel,) = tmp_path.glob("*.whl")
    shipped = {name for name in zipfile.ZipFile(wheel).namelist() if name.startswith("agentic_owasp/rules/")}
    expected = {f"agentic_owasp/rules/mcp-security/{r.source.parent.name}/{r.source.name}" for r in load_rules()}
    assert shipped == expected
