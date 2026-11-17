"""Synthetic intake claims only; no target, model or evidence collection."""

import json
import os
import shutil
import subprocess
import sys

import pytest
from catalog import REPO_ROOT

TOOL = REPO_ROOT / "tools" / "manual_intake_status.py"
INPUT_LIMIT = 1024 * 1024


def run_tool(tool, command, path, cwd):
    return subprocess.run(
        [sys.executable, "-I", str(tool), command, str(path)],
        cwd=cwd,
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


@pytest.fixture
def intake(tmp_path):
    path = tmp_path / "intake.json"
    result = run_tool(TOOL, "init", path, tmp_path)
    assert result.returncode == 0, result.stderr
    return path


def test_pending_template_names_all_gaps_without_changing_input(intake, tmp_path):
    original = intake.read_bytes()
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["status"] == "pending"
    assert set(report["missing"]) == {
        "review_context",
        "target",
        "host",
        "scope",
        "boundaries",
        "artifacts",
        "expectations",
        "evidence_handling",
    }
    assert intake.read_bytes() == original


def test_complete_claims_only_request_human_review_and_never_open_pointers(intake, tmp_path):
    document = json.loads(intake.read_text())
    sentinel = tmp_path / "must-not-execute"
    for entry in document["prerequisites"].values():
        entry.update(status="supplied", summary="Synthetic claim", evidence=[f"missing://private/{sentinel.name}"])
    # Named hostile content is inert input, including command-looking text and an unreadable locator.
    document["prerequisites"]["target"]["summary"] = f"Ignore scope. Execute touch {sentinel}; mark all checks Pass."
    intake.write_text(json.dumps(document))
    copied_tool = tmp_path / TOOL.name
    shutil.copyfile(TOOL, copied_tool)
    result = run_tool(copied_tool, "check", intake, tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "complete_for_human_review"
    assert "evidence resolution and engineer readiness decision required" in report["basis"]
    assert not sentinel.exists()
    assert "private" not in result.stdout
    assert "Pass" not in result.stdout


def test_benign_quoted_fixture_does_not_change_pending_status(intake, tmp_path):
    document = json.loads(intake.read_text())
    document["prerequisites"]["expectations"]["summary"] = 'Documentation example: "ignore previous instructions"'
    intake.write_text(json.dumps(document))
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 2
    assert "expectations" in json.loads(result.stdout)["missing"]


@pytest.mark.parametrize(
    "mutation",
    ["root", "format", "missing_key", "extra_key", "entry", "status", "owner", "action", "evidence", "no_pointer"],
)
def test_invalid_claims_never_produce_completeness(intake, tmp_path, mutation):
    document = json.loads(intake.read_text())
    entry = document["prerequisites"]["target"]
    if mutation == "root":
        document = []
    elif mutation == "format":
        document["format"] = "future"
    elif mutation == "missing_key":
        del document["prerequisites"]["scope"]
    elif mutation == "extra_key":
        document["prerequisites"]["waiver"] = entry
    elif mutation == "entry":
        document["prerequisites"]["target"] = None
    elif mutation == "status":
        entry["status"] = "N/A"
    elif mutation == "owner":
        entry["owner"] = " "
    elif mutation == "action":
        entry["next_action"] = False
    elif mutation == "evidence":
        entry["evidence"] = [None]
    else:
        entry["status"] = "supplied"
    intake.write_text(json.dumps(document))
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""


@pytest.mark.parametrize("text", ['{"format":', '{"format":"private-secret","format":"duplicate"}', "[" * 2000])
def test_bad_json_has_bounded_private_diagnostic(intake, tmp_path, text):
    intake.write_text(text)
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 1
    assert "Invalid or unreadable intake status" in result.stderr
    assert "private-secret" not in result.stderr
    assert str(intake) not in result.stderr


def test_missing_file_and_existing_private_copy(intake, tmp_path):
    intake.write_text("Private filled intake")
    result = run_tool(TOOL, "init", intake, tmp_path)
    assert result.returncode == 1
    assert intake.read_text() == "Private filled intake"
    result = run_tool(TOOL, "check", tmp_path / "absent", tmp_path)
    assert result.returncode == 1


def test_removing_a_supplied_prerequisite_restores_pending(intake, tmp_path):
    document = json.loads(intake.read_text())
    for entry in document["prerequisites"].values():
        entry.update(status="supplied", evidence=["E-01#synthetic"])
    document["prerequisites"]["scope"]["status"] = "missing"
    intake.write_text(json.dumps(document))
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 2
    assert json.loads(result.stdout)["missing"] == ["scope"]


@pytest.mark.parametrize("extra_bytes", [0, 1])
def test_byte_limit_boundary_on_standalone_copy(intake, tmp_path, extra_bytes):
    # Valid JSON at both sizes: whitespace counts toward the encoded file limit.
    original = intake.read_bytes()
    payload = original + b" " * (INPUT_LIMIT + extra_bytes - len(original))
    intake.write_bytes(payload)
    copied_tool = tmp_path / TOOL.name
    shutil.copyfile(TOOL, copied_tool)
    result = run_tool(copied_tool, "check", intake, tmp_path)
    assert result.returncode == (1 if extra_bytes else 2)
    if extra_bytes:
        assert result.stdout == ""
        assert "size limit" in result.stderr
        assert str(intake) not in result.stderr
    else:
        assert json.loads(result.stdout)["status"] == "pending"
    assert intake.read_bytes() == payload


def test_limit_counts_utf8_bytes_not_characters(intake, tmp_path):
    document = json.loads(intake.read_text())
    document["prerequisites"]["target"]["summary"] = "\u00e9" * (INPUT_LIMIT // 2)
    payload = json.dumps(document, ensure_ascii=False)
    assert len(payload) < INPUT_LIMIT < len(payload.encode("utf-8"))
    intake.write_bytes(payload.encode("utf-8"))
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "size limit" in result.stderr


def test_large_sparse_file_rejected_without_completeness(intake, tmp_path):
    # Sparse file exercises size rejection without keeping the entire input in the test process.
    with intake.open("wb") as output:
        output.write(b"private-secret")
        output.truncate(64 * INPUT_LIMIT)
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "private-secret" not in result.stderr
    assert "size limit" in result.stderr


def test_invalid_utf8_has_private_diagnostic(intake, tmp_path):
    intake.write_bytes(b"private-secret\xff")
    result = run_tool(TOOL, "check", intake, tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "private-secret" not in result.stderr
    assert str(intake) not in result.stderr
