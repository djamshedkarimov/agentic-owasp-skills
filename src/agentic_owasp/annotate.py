import json
import sys
from pathlib import Path

_DATA_ESCAPES = {"%": "%25", "\r": "%0D", "\n": "%0A"}
_PROPERTY_ESCAPES = {**_DATA_ESCAPES, ":": "%3A", ",": "%2C"}


def workflow_commands(sarif: dict) -> list[str]:
    commands = []
    for run in sarif["runs"]:
        for result in run["results"]:
            location = result["locations"][0]["physicalLocation"]
            region = location["region"]
            properties = {
                "file": location["artifactLocation"]["uri"],
                "line": region["startLine"],
                "col": region["startColumn"],
                "endLine": region["endLine"],
                "endColumn": region["endColumn"],
                "title": result["ruleId"],
            }
            rendered = ",".join(f"{key}={_escape(str(value), _PROPERTY_ESCAPES)}" for key, value in properties.items())
            message = _escape(result["message"]["text"], _DATA_ESCAPES)
            commands.append(f"::{result['level']} {rendered}::{message}")
    return commands


def _escape(value: str, escapes: dict[str, str]) -> str:
    # "%" is first in both tables, so earlier escapes are never re-escaped.
    for raw, escaped in escapes.items():
        value = value.replace(raw, escaped)
    return value


if __name__ == "__main__":
    for command in workflow_commands(json.loads(Path(sys.argv[1]).read_text())):
        print(command)
