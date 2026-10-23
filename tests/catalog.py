from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "mcp-security"
RULES_DIR = SKILL_DIR / "rules"
CROSSWALK = SKILL_DIR / "crosswalk.md"


@dataclass(frozen=True)
class Rule:
    id: str
    source: Path
    severity: str
    metadata: dict[str, Any]
    body: dict[str, Any]


def load_rules() -> list[Rule]:
    return [
        Rule(rule["id"], path, rule["severity"], rule["metadata"], rule)
        for path in sorted(RULES_DIR.glob("*/*.yaml"))
        for rule in yaml.safe_load(path.read_text())["rules"]
    ]
