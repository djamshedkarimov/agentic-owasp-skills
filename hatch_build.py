from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class RulesBuildHook(BuildHookInterface):
    """Bundle rule YAML into the wheel, leaving out the deliberately vulnerable test files beside it."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        # Editable installs read rules from the checkout so edits apply without a reinstall.
        if version == "editable":
            return
        for rule_file in Path(self.root).glob("skills/*/rules/*/*.yaml"):
            skill, language = rule_file.parts[-4], rule_file.parts[-2]
            build_data["force_include"][str(rule_file)] = f"agentic_owasp/rules/{skill}/{language}/{rule_file.name}"
