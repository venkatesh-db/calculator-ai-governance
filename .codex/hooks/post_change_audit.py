#!/usr/bin/env python3
"""Record AI code changes and verify fresh AGENTS.md ledger evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS_FILE = PROJECT_ROOT / "AGENTS.md"
CHANGELOG_FILE = PROJECT_ROOT / ".codex" / "AI_CHANGELOG.jsonl"
AUDITED_SUFFIXES = {".py", ".toml", ".json", ".yaml", ".yml", ".sh"}
AUDITED_NAMES = {"SKILL.md"}
EXCLUDED_PATHS = {"AGENTS.md", ".codex/AI_CHANGELOG.jsonl"}
PATCH_FILE_PATTERN = re.compile(
    r"^\*\*\* (Add|Update|Delete|Move) File:\s*(.+?)\s*$", re.MULTILINE
)
LEDGER_ROW_PATTERN = re.compile(
    r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*"
    r"(ADDED|MODIFIED|RENAMED|MOVED|DELETED)\s*\|\s*`([^`]+)`\s*\|",
    re.MULTILINE,
)
SHELL_WRITE_PATTERN = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:sed\s+-i|perl\s+-pi|rm|mv|cp|install|truncate)\b"
    r"|(?:>>?|write_text\s*\(|open\s*\([^\n]*[wa]['\"])",
)
SHELL_PATH_PATTERN = re.compile(
    r"(?P<path>(?:\.?\.?/|/)?[A-Za-z0-9_.\-/]+"
    r"(?:\.py|\.toml|\.json|\.ya?ml|\.sh|/SKILL\.md))\b"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for nested in value.values():
            result.extend(_strings(nested))
        return result
    if isinstance(value, list):
        result = []
        for nested in value:
            result.extend(_strings(nested))
        return result
    return []


def _relative_path(raw_path: str) -> str | None:
    candidate = Path(raw_path.strip())
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(PROJECT_ROOT)
        except ValueError:
            return None
    normalized = candidate.as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized.startswith("../"):
        return None
    return normalized


def _is_audited(path: str) -> bool:
    if path in EXCLUDED_PATHS or "__pycache__" in Path(path).parts:
        return False
    candidate = Path(path)
    return candidate.suffix in AUDITED_SUFFIXES or candidate.name in AUDITED_NAMES


def _changes(payload: dict[str, Any]) -> tuple[dict[str, str], set[str], str]:
    tool_name = str(payload.get("tool_name", "unknown"))
    tool_input = payload.get("tool_input", payload)
    values = _strings(tool_input)
    changes: dict[str, str] = {}
    ledger_additions: set[str] = set()

    for value in values:
        for action, raw_path in PATCH_FILE_PATTERN.findall(value):
            path = _relative_path(raw_path)
            if path:
                changes[path] = {
                    "Add": "ADDED",
                    "Update": "MODIFIED",
                    "Delete": "DELETED",
                    "Move": "MOVED",
                }[action]
        for line in value.splitlines():
            if line.startswith("+"):
                match = LEDGER_ROW_PATTERN.match(line[1:])
                if match:
                    ledger_additions.add(match.group(2))

    if tool_name.lower() in {"write", "edit", "multiedit"}:
        for value in values:
            path = _relative_path(value)
            if path and _is_audited(path):
                changes.setdefault(path, "MODIFIED")

    if tool_name.lower() in {"exec_command", "bash", "shell"}:
        for value in values:
            if not SHELL_WRITE_PATTERN.search(value):
                continue
            for match in SHELL_PATH_PATTERN.finditer(value):
                path = _relative_path(match.group("path"))
                if path and _is_audited(path):
                    changes.setdefault(path, "MODIFIED")

    return changes, ledger_additions, tool_name


def _ledger_counts() -> dict[str, int]:
    text = AGENTS_FILE.read_text() if AGENTS_FILE.is_file() else ""
    counts: dict[str, int] = {}
    for _, path in LEDGER_ROW_PATTERN.findall(text):
        counts[path] = counts.get(path, 0) + 1
    return counts


def _read_events() -> list[dict[str, Any]]:
    if not CHANGELOG_FILE.is_file():
        return []
    events = []
    for line in CHANGELOG_FILE.read_text().splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def _append_event(event: dict[str, Any]) -> None:
    CHANGELOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHANGELOG_FILE.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")


def _resolve_pending(counts: dict[str, int]) -> list[str]:
    events = _read_events()
    resolved_ids = {
        str(event["change_event_id"])
        for event in events
        if event.get("event") == "ledger_verified"
    }
    resolved: list[str] = []
    for event in events:
        if event.get("event") != "code_change" or event.get("id") in resolved_ids:
            continue
        pending = [item for item in event.get("files", []) if item["ledger_status"] == "pending"]
        if pending and all(counts.get(item["path"], 0) > item["ledger_count"] for item in pending):
            _append_event(
                {
                    "event": "ledger_verified",
                    "timestamp": _now(),
                    "change_event_id": event["id"],
                    "files": [item["path"] for item in pending],
                }
            )
            resolved.extend(item["path"] for item in pending)
    return resolved


def _feedback(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        _feedback(f"AI change audit could not read hook input: {exc}")
        return 0

    changes, ledger_additions, tool_name = _changes(payload)
    counts = _ledger_counts()
    agents_changed = "AGENTS.md" in changes
    audited_changes = {path: kind for path, kind in changes.items() if _is_audited(path)}

    pending: list[str] = []
    if audited_changes:
        files = []
        for path, change_type in sorted(audited_changes.items()):
            project_path = PROJECT_ROOT / path
            verified = path in ledger_additions
            if not verified:
                pending.append(path)
            files.append(
                {
                    "path": path,
                    "change_type": change_type,
                    "exists": project_path.exists(),
                    "sha256": _sha256(project_path),
                    "ledger_status": "verified_same_tool" if verified else "pending",
                    "ledger_count": counts.get(path, 0),
                }
            )
        _append_event(
            {
                "event": "code_change",
                "id": str(uuid4()),
                "timestamp": _now(),
                "actor": "codex-agent",
                "tool": tool_name,
                "files": files,
            }
        )

    resolved = _resolve_pending(counts) if agents_changed else []
    if pending:
        _feedback(
            "AI change evidence recorded, but fresh AGENTS.md ledger rows are pending for: "
            + ", ".join(pending)
            + ". Add one ledger row per file in the next change."
        )
    elif resolved:
        _feedback("AGENTS.md ledger evidence verified for: " + ", ".join(resolved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
