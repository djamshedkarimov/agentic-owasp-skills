import re

import yaml
from catalog import CROSSWALK, SKILL_DIR, load_rules

SKILL = SKILL_DIR / "SKILL.md"
CHECKLIST = SKILL_DIR / "checklist.md"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _frontmatter() -> dict:
    _, frontmatter, _ = SKILL.read_text().split("---\n", 2)
    return yaml.safe_load(frontmatter)


def _controls(path, pattern: str) -> dict[int, str]:
    return {int(n): name.strip() for n, name in re.findall(pattern, path.read_text(), re.MULTILINE)}


def test_frontmatter_declares_name_and_version() -> None:
    frontmatter = _frontmatter()
    assert frontmatter["name"] == SKILL_DIR.name
    assert frontmatter["description"]
    assert SEMVER.match(frontmatter["metadata"]["version"])


def test_checklist_covers_every_crosswalk_control() -> None:
    crosswalk = _controls(CROSSWALK, r"^\| (\d+) \| ([^|]+) \|")
    checklist = _controls(CHECKLIST, r"^## (\d+)\. (.+)$")
    assert checklist == crosswalk
    assert sorted(crosswalk) == list(range(1, 13))


def test_checklist_names_every_rule_under_its_control() -> None:
    sections = re.split(r"^## (?=\d+\. )", CHECKLIST.read_text(), flags=re.MULTILINE)
    by_control = {int(section.split(".", 1)[0]): section for section in sections[1:]}
    for rule in load_rules():
        assert f"`{rule.id}`" in by_control[rule.metadata["cheat-sheet-control"]], rule.id
