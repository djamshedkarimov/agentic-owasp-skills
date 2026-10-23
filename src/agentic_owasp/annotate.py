import json
import sys
from pathlib import Path

_DATA_ESCAPES = {"%": "%25", "\r": "%0D", "\n": "%0A"}
_PROPERTY_ESCAPES = {**_DATA_ESCAPES, ":": "%3A", ",": "%2C"}
_COMMAND = {"error": "error", "warning": "warning", "note": "notice"}


def workflow_commands(sarif: dict) -> list[str]:
    commands = []
    for run in sarif["runs"]:
        for result in run["results"]:
            commands.append(_command(result["level"], result["ruleId"], result["message"]["text"], result["locations"]))
        for invocation in run.get("invocations", []):
            for notification in invocation.get("toolExecutionNotifications", []):
                title = notification.get("descriptor", {}).get("id", "agentic-owasp")
                locations = notification.get("locations", [])
                commands.append(_command(notification["level"], title, notification["message"]["text"], locations))
    return commands


def _command(level: str, title: str, text: str, locations: list[dict]) -> str:
    properties = {}
    if locations:
        location = locations[0]["physicalLocation"]
        region = location["region"]
        properties = {
            "file": location["artifactLocation"]["uri"],
            "line": region["startLine"],
            "col": region["startColumn"],
            "endLine": region["endLine"],
            "endColumn": region["endColumn"],
        }
    properties["title"] = title
    rendered = ",".join(f"{key}={_escape(str(value), _PROPERTY_ESCAPES)}" for key, value in properties.items())
    return f"::{_COMMAND[level]} {rendered}::{_escape(text, _DATA_ESCAPES)}"


def _escape(value: str, escapes: dict[str, str]) -> str:
    # "%" is first in both tables, so earlier escapes are never re-escaped.
    for raw, escaped in escapes.items():
        value = value.replace(raw, escaped)
    return value


if __name__ == "__main__":
    for command in workflow_commands(json.loads(Path(sys.argv[1]).read_text())):
        print(command)
