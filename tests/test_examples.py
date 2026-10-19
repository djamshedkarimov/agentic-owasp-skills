import asyncio
import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

import pytest
from catalog import REPO_ROOT, RULES_DIR, load_rules
from mcp.server.mcpserver import MCPServer

EXAMPLES_DIR = REPO_ROOT / "examples"
IMPLEMENTED_RULE_IDS = {rule.id for rule in load_rules()}
EXAMPLE_FILES = sorted(
    path for pattern in ("python/*.py", "typescript/*-server.ts") for path in EXAMPLES_DIR.glob(pattern)
)
ANNOTATION = re.compile(r"(?:#|//)\s*(?P<kind>ruleid|ok):\s*(?P<ids>[\w\-, ]+)$")
SAFE_SERVER_ENV = {
    "MCP_ISSUER_URL": "https://auth.example.com",
    "MCP_RESOURCE_URL": "https://mcp.example.com",
    "MCP_JWT_PUBLIC_KEY": "unused-at-import",
}


class Finding(NamedTuple):
    path: Path
    line: int
    rule_id: str


def expected_findings(path: Path) -> set[Finding]:
    """Semgrep test convention: a `ruleid:` annotation asserts a finding on the following line."""
    expected = set()
    for line_number, text in enumerate(path.read_text().splitlines(), start=1):
        match = ANNOTATION.search(text)
        if match and match["kind"] == "ruleid":
            expected |= {Finding(path, line_number + 1, rule_id.strip()) for rule_id in match["ids"].split(",")}
    return expected


@pytest.fixture(scope="session")
def scanned_findings() -> set[Finding]:
    semgrep = shutil.which("semgrep")
    assert semgrep, "semgrep not on PATH; run `make install`"
    result = subprocess.run(
        [
            semgrep,
            "scan",
            "--config",
            str(RULES_DIR),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            *map(str, EXAMPLE_FILES),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return {
        Finding(Path(match["path"]).resolve(), match["start"]["line"], match["check_id"].rsplit(".", 1)[-1])
        for match in json.loads(result.stdout)["results"]
    }


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda path: str(path.relative_to(EXAMPLES_DIR)))
def test_findings_match_annotations(path: Path, scanned_findings: set[Finding]) -> None:
    actual = {finding for finding in scanned_findings if finding.path == path}
    expected = {finding for finding in expected_findings(path) if finding.rule_id in IMPLEMENTED_RULE_IDS}
    assert actual == expected, f"missed: {sorted(expected - actual)}\nunexpected: {sorted(actual - expected)}"


def test_every_annotated_rule_is_implemented() -> None:
    annotated = {finding.rule_id for path in EXAMPLE_FILES for finding in expected_findings(path)}
    if pending := sorted(annotated - IMPLEMENTED_RULE_IDS):
        pytest.skip(f"rules not implemented yet: {', '.join(pending)}")


def test_every_vulnerable_example_has_a_safe_counterpart() -> None:
    names = {path.name for path in EXAMPLE_FILES}
    for path in EXAMPLE_FILES:
        if "vulnerable" in path.name:
            assert path.name.replace("vulnerable", "safe") in names


def test_safe_examples_assert_no_findings() -> None:
    for path in EXAMPLE_FILES:
        if "safe" in path.name:
            assert not expected_findings(path), f"{path.name} carries a ruleid annotation"


def _tool_names(server: MCPServer) -> set[str]:
    return {tool.name for tool in asyncio.run(server.list_tools())}


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_python_examples_expose_the_same_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in SAFE_SERVER_ENV.items():
        monkeypatch.setenv(name, value)
    vulnerable = _load_module(EXAMPLES_DIR / "python" / "vulnerable_server.py").mcp
    safe = _load_module(EXAMPLES_DIR / "python" / "safe_server.py").mcp

    assert _tool_names(vulnerable) == _tool_names(safe)
