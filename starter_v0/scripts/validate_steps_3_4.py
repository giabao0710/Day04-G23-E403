from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS, load_tool_declarations
from versioning import build_artifact_version


ALLOWED_FAILURES = {
    "wrong_tool",
    "wrong_arg_value",
    "wrong_boundary",
    "unnecessary_tool",
    "out_of_scope",
    "missing_info",
}
VERSIONS = {
    "v1": (ROOT / "artifacts/versions/v1/system_prompt.md", ROOT / "artifacts/versions/v1/tools.yaml"),
    "v2": (ROOT / "artifacts/versions/v2/system_prompt.md", ROOT / "artifacts/versions/v1/tools.yaml"),
    "v3": (ROOT / "artifacts/system_prompt.md", ROOT / "artifacts/tools.yaml"),
}


def validate_versions() -> None:
    artifacts = [build_artifact_version(version, *paths) for version, paths in VERSIONS.items()]
    if len({(item.prompt_hash, item.tools_hash) for item in artifacts}) != 3:
        raise ValueError("v1, v2, v3 must use three distinct artifact combinations.")
    with (ROOT / "artifacts/version_log.csv").open(encoding="utf-8", newline="") as file:
        log = {row["version"]: row for row in csv.DictReader(file)}
    for item in artifacts:
        row = log.get(item.version, {})
        if row.get("artifact_version") != item.artifact_version:
            raise ValueError(f"{item.version} hash does not match version_log.csv.")
        print(f"{item.version}: {item.artifact_version}")


def validate_group_eval() -> None:
    path = ROOT / "data/eval_group.json"
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    single = [case for case in cases if "query" in case]
    multi = [case for case in cases if "turns" in case]
    if len(cases) != 10 or len(single) != 5 or len(multi) != 5:
        raise ValueError("eval_group.json must contain exactly 5 query and 5 turns cases.")
    if len({case.get("id") for case in cases}) != 10:
        raise ValueError("Team eval case IDs must be unique.")

    declared = {item["name"] for item in load_tool_declarations(ROOT / "artifacts/tools.yaml")}
    for case in cases:
        required = case.get("phase") == "B" and case.get("failure_type") in ALLOWED_FAILURES
        required = required and bool(case.get("metadata", {}).get("what_it_tests"))
        expect = case.get("expect", {})
        required = required and (bool(expect.get("tool_calls")) != bool(expect.get("no_tool")))
        if not required:
            raise ValueError(f"Invalid required fields in {case.get('id')}.")
        if "turns" in case and (not case["turns"] or case["turns"][-1].get("role") != "user"):
            raise ValueError(f"{case['id']} must end with a user turn.")
        for call in expect.get("tool_calls", []):
            if call.get("name") not in declared or call.get("name") not in TOOL_FUNCTIONS:
                raise ValueError(f"{case['id']} references unavailable tool {call.get('name')!r}.")
    print("group eval: 10 cases (5 single-turn + 5 multi-turn)")


if __name__ == "__main__":
    validate_versions()
    validate_group_eval()
    print("OK: Steps 3-4 artifacts are structurally ready.")
