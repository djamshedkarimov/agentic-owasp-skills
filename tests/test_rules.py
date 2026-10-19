import re
from itertools import groupby

import pytest
from catalog import CROSSWALK, Rule, load_rules

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
