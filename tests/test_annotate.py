import json
from pathlib import Path

import pytest
from catalog import REPO_ROOT

from agentic_owasp.annotate import workflow_commands
from agentic_owasp.cli import main


def test_every_sarif_result_becomes_an_annotation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = tmp_path / "report.sarif"
    main(["scan", str(REPO_ROOT / "examples"), "--format", "sarif", "--output", str(report)])
    sarif = json.loads(report.read_text())
    commands = workflow_commands(sarif)
    assert len(commands) == len(sarif["runs"][0]["results"])
    assert all(command.startswith(("::error file=", "::warning file=")) for command in commands)
    assert any(",title=mcp-http-no-auth::" in command for command in commands)


def test_untrusted_values_cannot_break_out_of_the_command() -> None:
    sarif = {
        "runs": [
            {
                "results": [
                    {
                        "ruleId": "rule",
                        "level": "error",
                        "message": {"text": "100%\n::warning::injected"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "a,b:c.py"},
                                    "region": {"startLine": 1, "startColumn": 2, "endLine": 3, "endColumn": 4},
                                }
                            }
                        ],
                    }
                ]
            }
        ]
    }
    assert workflow_commands(sarif) == [
        "::error file=a%2Cb%3Ac.py,line=1,col=2,endLine=3,endColumn=4,title=rule::100%25%0A::warning::injected"
    ]
