#!/usr/bin/env python3
"""Require focused behavioral-test evidence before allowing cli.py edits."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI_FILE = PROJECT_ROOT / "cli.py"
PROJECT_KEY = hashlib.sha256(str(PROJECT_ROOT).encode()).hexdigest()[:16]
STATE_FILE = Path(tempfile.gettempdir()) / f"calculator-cli-change-gate-{PROJECT_KEY}.json"
MAX_EVIDENCE_AGE_SECONDS = 60 * 60


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _test_hashes() -> dict[str, str]:
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): _sha256(path)
        for path in sorted(PROJECT_ROOT.rglob("test*.py"))
        if "__pycache__" not in path.parts
    }


def _valid_test_result(exit_code: int, output: str) -> tuple[bool, str]:
    if "Ran " not in output:
        return False, "the command did not execute a unittest test case"
    if exit_code == 0 and "OK" in output:
        return True, "passed"
    if (
        exit_code == 1
        and "FAILED (failures=" in output
        and "ERROR:" not in output
        and "errors=" not in output
    ):
        return True, "failed by assertion as expected for a red test"
    return False, "the test had a setup/import error or an unsupported result"


def authorize(requirement: str, test_selector: str) -> int:
    if not requirement.strip():
        print("error: --requirement must describe the requested CLI behavior", file=sys.stderr)
        return 2
    if not test_selector.startswith("calculator."):
        print("error: --test must be a focused calculator unittest selector", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    existing_pythonpath = env.get("PYTHONPATH")
    parent = str(PROJECT_ROOT.parent)
    env["PYTHONPATH"] = (
        f"{parent}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else parent
    )
    command = [sys.executable, "-B", "-m", "unittest", "-v", test_selector]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    print(output, end="")

    valid, classification = _valid_test_result(completed.returncode, output)
    if not valid:
        print(f"CLI change gate not authorized: {classification}", file=sys.stderr)
        return 1

    state = {
        "version": 1,
        "authorized_at": int(time.time()),
        "requirement": requirement.strip(),
        "test_selector": test_selector,
        "test_exit_code": completed.returncode,
        "test_result": classification,
        "cli_sha256": _sha256(CLI_FILE),
        "test_sha256": _test_hashes(),
    }
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print(f"CLI change gate authorized: {classification}")
    return 0


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for nested in value.values():
            strings.extend(_string_values(nested))
        return strings
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_string_values(nested))
        return strings
    return []


def _targets_cli(payload: dict[str, Any]) -> bool:
    tool_input = payload.get("tool_input", payload)
    for value in _string_values(tool_input):
        if re.search(r"(?:Add|Update|Delete|Move) File:\s*[^\n]*[/\\]?cli\.py\b", value):
            return True
        candidate = Path(value)
        if candidate.name == "cli.py":
            return True
        if "cli.py" in value and re.search(
            r"(?:^|[;&|]\s*|\s)(?:sed\s+-i|perl\s+-pi|rm|mv|cp|install|truncate)\b"
            r"|(?:>>?|write_text\s*\(|open\s*\([^\n]*[wa]['\"])",
            value,
        ):
            return True
    return False


def _deny(reason: str) -> int:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(response))
    return 0


def hook() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        return _deny(f"CLI test-first gate could not read hook input: {exc}")

    if not _targets_cli(payload):
        return 0
    if not STATE_FILE.is_file():
        return _deny(
            "Run a requirement-specific CLI test before editing cli.py: "
            "python3 -B .codex/hooks/cli_test_gate.py authorize "
            "--requirement '<behavior>' --test '<focused unittest selector>'"
        )

    try:
        state = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return _deny(f"CLI test-first evidence is unreadable: {exc}")

    age = int(time.time()) - int(state.get("authorized_at", 0))
    if age < 0 or age > MAX_EVIDENCE_AGE_SECONDS:
        return _deny("CLI test-first evidence is stale; rerun the focused test")
    if state.get("cli_sha256") != _sha256(CLI_FILE):
        return _deny("cli.py changed after the focused test; rerun the test before editing again")
    if state.get("test_sha256") != _test_hashes():
        return _deny("CLI tests changed after authorization; rerun the focused test")
    if not state.get("requirement") or not state.get("test_selector"):
        return _deny("CLI test-first evidence does not identify the behavior and test")
    return 0


def clear() -> int:
    STATE_FILE.unlink(missing_ok=True)
    print("CLI change gate evidence cleared")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    authorize_parser = subparsers.add_parser("authorize")
    authorize_parser.add_argument("--requirement", required=True)
    authorize_parser.add_argument("--test", required=True, dest="test_selector")
    subparsers.add_parser("hook")
    subparsers.add_parser("clear")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "authorize":
        return authorize(args.requirement, args.test_selector)
    if args.command == "hook":
        return hook()
    return clear()


if __name__ == "__main__":
    raise SystemExit(main())
