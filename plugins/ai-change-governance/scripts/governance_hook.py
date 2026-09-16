#!/usr/bin/env python3
"""Vendor-neutral test-first gate and append-only AI change audit."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable
from uuid import uuid4


POLICY_NAME = ".ai-governance.json"
PATCH_PATTERN = re.compile(r"^\*\*\* (Add|Update|Delete|Move) File:\s*(.+?)\s*$", re.MULTILINE)
LEDGER_PATTERN = re.compile(
    r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*"
    r"(ADDED|MODIFIED|RENAMED|MOVED|DELETED)\s*\|\s*`([^`]+)`\s*\|",
    re.MULTILINE,
)
PATH_KEYS = {"file", "file_path", "path", "target", "destination", "old_path", "new_path"}
DEFAULT_SUFFIXES = [".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".sh", ".json", ".yaml", ".yml", ".toml"]
SHELL_WRITE_PATTERN = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:sed\s+-i|perl\s+-pi|rm|mv|cp|install|truncate)\b"
    r"|(?:>>?|write_text\s*\(|open\s*\([^\n]*[wa]['\"])",
)
SHELL_PATH_PATTERN = re.compile(
    r"(?P<path>(?:\.?\.?/|/)?[A-Za-z0-9_.\-/]+"
    r"(?:\.[A-Za-z0-9_]+|/SKILL\.md))\b",
)


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from strings(nested)


def find_policy(start: Path) -> Path | None:
    current = start.resolve()
    for directory in (current, *current.parents):
        candidate = directory / POLICY_NAME
        if candidate.is_file():
            return candidate
    return None


def load_policy(explicit: str | None, cwd: str | None = None) -> tuple[Path, dict[str, Any]] | None:
    policy_path = Path(explicit).resolve() if explicit else find_policy(Path(cwd or os.getcwd()))
    if policy_path is None:
        return None
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError("policy version must be 1")
    return policy_path.parent, data


def relative(raw: str, root: Path) -> str | None:
    candidate = Path(raw.strip().strip("'\""))
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(root)
        except ValueError:
            return None
    normalized = candidate.as_posix().removeprefix("./")
    return normalized if normalized and not normalized.startswith("../") else None


def extract_changes(payload: dict[str, Any], root: Path) -> dict[str, str]:
    changes: dict[str, str] = {}
    action_map = {"Add": "ADDED", "Update": "MODIFIED", "Delete": "DELETED", "Move": "MOVED"}
    for value in strings(payload.get("tool_input", payload)):
        for action, raw in PATCH_PATTERN.findall(value):
            path = relative(raw, root)
            if path:
                changes[path] = action_map[action]

    def visit(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for nested_key, nested in value.items():
                visit(nested, nested_key)
        elif isinstance(value, list):
            for nested in value:
                visit(nested, key)
        elif isinstance(value, str) and key in PATH_KEYS:
            path = relative(value, root)
            if path:
                changes.setdefault(path, "MODIFIED")

    visit(payload.get("tool_input", payload))
    for value in strings(payload.get("tool_input", payload)):
        if not SHELL_WRITE_PATTERN.search(value):
            continue
        for match in SHELL_PATH_PATTERN.finditer(value):
            path = relative(match.group("path"), root)
            if path:
                changes.setdefault(path, "MODIFIED")
    return changes


def ledger_additions(payload: dict[str, Any]) -> set[str]:
    additions: set[str] = set()
    for value in strings(payload.get("tool_input", payload)):
        for line in value.splitlines():
            candidate = line[1:] if line.startswith("+") else line
            match = LEDGER_PATTERN.match(candidate)
            if match:
                additions.add(match.group(2))
    return additions


def ledger_counts(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    counts: dict[str, int] = {}
    for _, item in LEDGER_PATTERN.findall(text):
        counts[item] = counts.get(item, 0) + 1
    return counts


def is_audited(path: str, policy: dict[str, Any]) -> bool:
    audit = policy.get("audit", {})
    excluded = set(audit.get("excluded_paths", []))
    suffixes = set(audit.get("suffixes", DEFAULT_SUFFIXES))
    names = set(audit.get("names", ["SKILL.md"]))
    candidate = Path(path)
    return path not in excluded and "__pycache__" not in candidate.parts and (candidate.suffix in suffixes or candidate.name in names)


def state_path(root: Path, policy: dict[str, Any]) -> Path:
    digest = hashlib.sha256(str(root).encode()).hexdigest()[:16]
    name = policy.get("state_file", f"ai-change-governance-{digest}.json")
    return Path(tempfile.gettempdir()) / Path(name).name


def evidence_hashes(root: Path, patterns: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and "__pycache__" not in path.parts:
                result[path.relative_to(root).as_posix()] = sha256(path) or ""
    return result


def authorize(args: argparse.Namespace) -> int:
    loaded = load_policy(args.policy)
    if loaded is None:
        print(f"error: no {POLICY_NAME} found", file=sys.stderr)
        return 2
    root, policy = loaded
    protected = policy.get("test_first", {}).get("protected_files", {})
    rule = protected.get(args.file)
    if not rule:
        print(f"error: {args.file} is not protected by this policy", file=sys.stderr)
        return 2
    if not args.requirement.strip() or not args.command:
        print("error: requirement and test command are required", file=sys.stderr)
        return 2
    command = args.command[1:] if args.command[0] == "--" else args.command
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    output = completed.stdout + completed.stderr
    print(output, end="")
    valid_codes = set(rule.get("valid_exit_codes", [0]))
    assertion_markers = rule.get("assertion_failure_markers", [])
    assertion_failure = completed.returncode == 1 and assertion_markers and any(marker in output for marker in assertion_markers)
    if completed.returncode not in valid_codes and not assertion_failure:
        print("authorization denied: test did not produce an accepted result", file=sys.stderr)
        return 1
    watched = rule.get("watch", [args.file, "test*"])
    state = {
        "version": 1,
        "authorized_at": int(time.time()),
        "file": args.file,
        "requirement": args.requirement.strip(),
        "command": command,
        "exit_code": completed.returncode,
        "hashes": evidence_hashes(root, watched),
    }
    state_path(root, policy).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("protected-file change authorized")
    return 0


def valid_authorization(path: str, root: Path, policy: dict[str, Any]) -> tuple[bool, str]:
    rule = policy.get("test_first", {}).get("protected_files", {}).get(path, {})
    state_file = state_path(root, policy)
    if not state_file.is_file():
        return False, f"Run the configured focused test before modifying {path}."
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "Authorization evidence is unreadable; rerun the focused test."
    max_age = int(rule.get("max_age_seconds", 3600))
    if state.get("file") != path or int(time.time()) - int(state.get("authorized_at", 0)) not in range(max_age + 1):
        return False, "Authorization evidence is stale or belongs to another file."
    current = evidence_hashes(root, rule.get("watch", [path, "test*"]))
    if current != state.get("hashes"):
        return False, "Protected source or watched tests changed; rerun the focused test."
    return True, ""


def response(provider: str, event: str, *, deny: str | None = None, context: str | None = None) -> dict[str, Any]:
    if deny:
        if provider == "gemini":
            return {"decision": "deny", "reason": deny}
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": deny}}
    if context:
        output: dict[str, Any] = {"additionalContext": context}
        if provider != "gemini":
            output["hookEventName"] = "PostToolUse"
        return {"hookSpecificOutput": output}
    return {}


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")


def resolve_pending(changelog: Path, counts: dict[str, int]) -> list[str]:
    if not changelog.is_file():
        return []
    events = [json.loads(line) for line in changelog.read_text(encoding="utf-8").splitlines() if line.strip()]
    resolved_ids = {event["change_event_id"] for event in events if event.get("event") == "ledger_verified"}
    resolved: list[str] = []
    for event in events:
        if event.get("event") != "code_change" or event.get("id") in resolved_ids:
            continue
        pending = [item for item in event.get("files", []) if item.get("ledger_status") == "pending"]
        if pending and all(counts.get(item["path"], 0) > item["ledger_count"] for item in pending):
            append_event(changelog, {"event": "ledger_verified", "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "change_event_id": event["id"], "files": [item["path"] for item in pending]})
            resolved.extend(item["path"] for item in pending)
    return resolved


def hook(args: argparse.Namespace) -> int:
    try:
        payload = json.load(sys.stdin)
        loaded = load_policy(args.policy, payload.get("cwd"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps(response(args.provider, args.event, deny=f"Governance hook configuration error: {exc}")))
        return 0
    if loaded is None:
        print("{}")
        return 0
    root, policy = loaded
    changes = extract_changes(payload, root)
    if args.event == "pre":
        for path in changes:
            if path in policy.get("test_first", {}).get("protected_files", {}):
                valid, reason = valid_authorization(path, root, policy)
                if not valid:
                    print(json.dumps(response(args.provider, args.event, deny=reason)))
                    return 0
        print("{}")
        return 0

    audit = policy.get("audit", {})
    ledger = root / audit.get("ledger_file", "AGENTS.md")
    changelog = root / audit.get("changelog_file", ".ai-governance/AI_CHANGELOG.jsonl")
    counts = ledger_counts(ledger)
    additions = ledger_additions(payload)
    pending: list[str] = []
    files = []
    for path, kind in sorted(changes.items()):
        if not is_audited(path, policy):
            continue
        verified = path in additions
        if not verified:
            pending.append(path)
        project_path = root / path
        files.append({"path": path, "change_type": kind, "exists": project_path.exists(), "sha256": sha256(project_path), "ledger_status": "verified_same_tool" if verified else "pending", "ledger_count": counts.get(path, 0)})
    if files:
        append_event(changelog, {"event": "code_change", "id": str(uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "actor": args.provider, "tool": payload.get("tool_name", "unknown"), "files": files})
    resolved = resolve_pending(changelog, counts) if ledger.relative_to(root).as_posix() in changes else []
    message = None
    if pending:
        message = "Change evidence recorded; add fresh ledger entries for: " + ", ".join(pending)
    elif resolved:
        message = "Ledger evidence verified for: " + ", ".join(resolved)
    print(json.dumps(response(args.provider, args.event, context=message) if message else {}))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="action", required=True)
    auth = sub.add_parser("authorize")
    auth.add_argument("--policy")
    auth.add_argument("--file", required=True)
    auth.add_argument("--requirement", required=True)
    auth.add_argument("command", nargs=argparse.REMAINDER)
    run = sub.add_parser("hook")
    run.add_argument("--policy")
    run.add_argument("--provider", choices=("codex", "claude", "gemini", "generic"), required=True)
    run.add_argument("--event", choices=("pre", "post"), required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    return authorize(args) if args.action == "authorize" else hook(args)


if __name__ == "__main__":
    raise SystemExit(main())
