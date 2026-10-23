import re
import subprocess
from itertools import groupby
from typing import Any

import pytest
from catalog import CROSSWALK, RULES_DIR, Rule, load_rules

from agentic_owasp.scanner import find_semgrep

RULES = load_rules()
MCP_IDS = {f"MCP{n:02}" for n in range(1, 11)}
AGENTIC_IDS = {f"ASI{n:02}" for n in range(1, 11)}
ID_PATTERNS = {"mcp": r"MCP\d{2}", "asi": r"ASI\d{2}", "rules": r"mcp-[a-z-]+"}
CROSSWALK_ROW = re.compile(
    r"^\| (?P<control>\d+) \| [^|]+ \| (?P<mcp>[^|]+) \| (?P<asi>[^|]+) \|(?:[^|]+\|){2} (?P<rules>[^|]+) \|$"
)


def _crosswalk() -> dict[int, dict[str, set[str]]]:
    rows = {}
    for line in CROSSWALK.read_text().splitlines():
        if match := CROSSWALK_ROW.match(line):
            rows[int(match["control"])] = {
                column: set(re.findall(pattern, match[column])) for column, pattern in ID_PATTERNS.items()
            }
    return rows


CROSSWALK_ROWS = _crosswalk()


@pytest.mark.parametrize("rule", RULES, ids=lambda rule: f"{rule.source.parent.name}/{rule.id}")
def test_rule_metadata_is_valid(rule: Rule) -> None:
    metadata = rule.metadata
    assert rule.id.startswith("mcp-")
    assert rule.severity in {"ERROR", "WARNING"}
    assert metadata["cheat-sheet-control"] in CROSSWALK_ROWS
    assert metadata["owasp-mcp"] and set(metadata["owasp-mcp"]) <= MCP_IDS
    assert metadata["owasp-agentic"] and set(metadata["owasp-agentic"]) <= AGENTIC_IDS
    assert all(re.fullmatch(r"CWE-\d+", cwe) for cwe in metadata["cwe"])
    assert metadata["confidence"] in {"HIGH", "MEDIUM", "LOW"}
    assert metadata["references"]


@pytest.mark.parametrize("rule", RULES, ids=lambda rule: f"{rule.source.parent.name}/{rule.id}")
def test_rule_agrees_with_crosswalk(rule: Rule) -> None:
    row = CROSSWALK_ROWS[rule.metadata["cheat-sheet-control"]]
    assert rule.id in row["rules"]
    assert set(rule.metadata["owasp-mcp"]) <= row["mcp"]
    assert set(rule.metadata["owasp-agentic"]) <= row["asi"]


def test_crosswalk_lists_only_implemented_rules() -> None:
    listed = set().union(*(row["rules"] for row in CROSSWALK_ROWS.values()))
    assert listed == {rule.id for rule in RULES}


def test_rule_ids_are_unique_per_language() -> None:
    keys = [(rule.source.parent.name, rule.id) for rule in RULES]
    assert len(keys) == len(set(keys))


def test_same_rule_has_same_classification_across_languages() -> None:
    for rule_id, variants in groupby(sorted(RULES, key=lambda rule: rule.id), key=lambda rule: rule.id):
        assert len({repr((rule.severity, rule.metadata)) for rule in variants}) == 1, rule_id


def _name_regexes(node: Any) -> set[str]:
    if isinstance(node, dict):
        if node.get("metavariable") == "$NAME" and "regex" in node:
            return {node["regex"]}
        return set().union(*(_name_regexes(value) for value in node.values()))
    if isinstance(node, list):
        return set().union(*(_name_regexes(item) for item in node))
    return set()


@pytest.mark.parametrize("language", ["python", "typescript"])
def test_secret_name_regex_is_identical_across_rules(language: str) -> None:
    # Duplicated on purpose: semgrep-core's YAML parser does not resolve an alias used as a regex.
    by_id = {rule.id: rule for rule in RULES if rule.source.parent.name == language}
    (hardcoded,) = _name_regexes(by_id["mcp-hardcoded-secret"].body)
    assert hardcoded in _name_regexes(by_id["mcp-secret-in-log"].body)


def test_rules_pass_semgrep_core_validation() -> None:
    command = [find_semgrep(), "scan", "--config", str(RULES_DIR), "--json", "--metrics=off", "--disable-version-check"]
    completed = subprocess.run([*command, str(RULES_DIR)], capture_output=True, text=True, check=True)
    assert "RuleParseError" not in completed.stderr, completed.stderr
