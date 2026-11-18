"""Check self-reported intake completeness, never target security or evidence validity."""

import argparse
import json
from pathlib import Path

FORMAT = "manual-intake-status-v1"
MAX_INPUT_BYTES = 1024 * 1024
PREREQUISITES = {
    "review_context": "Record assessment/owner, workflow revision and baseline review method/effort",
    "target": "Identify one non-MCP target, source revision and artifact identity",
    "host": "Declare review product/version, OS and installation method",
    "scope": "Declare permitted read-only artifacts/paths, access and exclusions",
    "boundaries": "Describe actual components, identities, data/actions and trust boundaries",
    "artifacts": "Inventory available/inaccessible evidence with collection and alteration provenance",
    "expectations": "Record engineer questions and expected application security behavior",
    "evidence_handling": "Name private storage, sharing/redaction rules and retention owner",
}
ENTRY_FIELDS = {"status", "summary", "evidence", "owner", "next_action"}


def template() -> dict:
    return {
        "format": FORMAT,
        "prerequisites": {
            key: {
                "status": "missing",
                "summary": description,
                "evidence": [],
                "owner": "Assign intake owner",
                "next_action": description,
            }
            for key, description in PREREQUISITES.items()
        },
    }


def unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check(document: object) -> dict:
    if not isinstance(document, dict) or set(document) != {"format", "prerequisites"}:
        raise ValueError("Expected format and prerequisites fields only")
    if document["format"] != FORMAT:
        raise ValueError("Unsupported intake status format")
    entries = document["prerequisites"]
    if not isinstance(entries, dict) or set(entries) != set(PREREQUISITES):
        raise ValueError("Expected the fixed eight prerequisite IDs")
    missing = []
    for key in PREREQUISITES:
        entry = entries[key]
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            raise ValueError(f"{key}: invalid entry fields")
        if entry["status"] not in ("missing", "supplied"):
            raise ValueError(f"{key}: status must be missing or supplied")
        for field in ("summary", "owner", "next_action"):
            if not nonempty(entry[field]):
                raise ValueError(f"{key}: {field} must be nonempty text")
        pointers = entry["evidence"]
        if not isinstance(pointers, list) or not all(nonempty(pointer) for pointer in pointers):
            raise ValueError(f"{key}: evidence must be a list of nonempty pointer strings")
        if entry["status"] == "supplied" and not pointers:
            raise ValueError(f"{key}: supplied requires at least one evidence pointer")
        if entry["status"] == "missing":
            missing.append(key)
    # No supplied text is echoed or interpreted. Evidence pointers are never opened.
    return {
        "format": FORMAT,
        "status": "pending" if missing else "complete_for_human_review",
        "missing": missing,
        "basis": "self-reported fields only; evidence resolution and engineer readiness decision required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init", help="Create a private pending template; never overwrite")
    initialize.add_argument("file", type=Path)
    inspect = commands.add_parser("check", help="Check explicit fields without opening referenced artifacts")
    inspect.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            with args.file.open("x", encoding="utf-8") as output:
                output.write(json.dumps(template(), indent=2) + "\n")
            print("Pending intake template created; fill privately and obtain human review.")
            return
        with args.file.open("rb") as source:
            payload = source.read(MAX_INPUT_BYTES + 1)
        if len(payload) > MAX_INPUT_BYTES:
            raise ValueError("Intake status exceeds byte limit")
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object)
        result = check(document)
    except (OSError, ValueError, RecursionError):
        # Parser/I/O messages can contain private paths or supplied text. Keep CLI diagnostics bounded.
        parser.exit(
            1, "Invalid or unreadable intake status; check the size limit, format and required fields in the guide.\n"
        )
    print(json.dumps(result, indent=2))
    raise SystemExit(2 if result["missing"] else 0)


if __name__ == "__main__":
    main()
