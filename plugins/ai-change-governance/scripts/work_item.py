#!/usr/bin/env python3
"""Create and transition evidence-bearing organizational work items."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


WORKFLOW_FILE = Path(__file__).resolve().parents[1] / "workflow" / "role-workflow.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def create(args: argparse.Namespace) -> dict[str, Any]:
    if args.file.exists():
        raise ValueError(f"refusing to overwrite existing work item: {args.file}")
    if not args.criterion:
        raise ValueError("at least one --criterion is required")
    timestamp = now()
    return {
        "version": 1,
        "id": args.id,
        "title": args.title,
        "outcome": args.outcome,
        "status": "intake",
        "acceptance_criteria": args.criterion,
        "constraints": args.constraint,
        "assumptions": [],
        "decisions": [],
        "handoffs": [],
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def transition(item: dict[str, Any], args: argparse.Namespace, workflow: dict[str, Any]) -> dict[str, Any]:
    current = item.get("status")
    allowed = workflow["transitions"].get(current, [])
    if args.to not in allowed:
        raise ValueError(f"transition {current!r} -> {args.to!r} is not allowed")
    permitted = workflow["roles"].get(args.role, [])
    if args.to not in permitted:
        raise ValueError(f"role {args.role!r} cannot transition work to {args.to!r}")
    if args.to == "architecture-ready" and (not item.get("outcome") or not item.get("acceptance_criteria")):
        raise ValueError("architecture-ready requires an outcome and acceptance criteria")
    if args.to in workflow.get("required_evidence", {}) and args.to != "architecture-ready" and not args.evidence:
        raise ValueError(f"{args.to} requires at least one --evidence entry")
    timestamp = now()
    updated = dict(item)
    updated["status"] = args.to
    updated["updated_at"] = timestamp
    handoffs = list(item.get("handoffs", []))
    handoffs.append({
        "from": current,
        "to": args.to,
        "role": args.role,
        "summary": args.summary,
        "evidence": args.evidence,
        "timestamp": timestamp,
    })
    updated["handoffs"] = handoffs
    return updated


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new")
    new.add_argument("--file", type=Path, required=True)
    new.add_argument("--id", required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--outcome", required=True)
    new.add_argument("--criterion", action="append", default=[])
    new.add_argument("--constraint", action="append", default=[])
    move = sub.add_parser("transition")
    move.add_argument("--file", type=Path, required=True)
    move.add_argument("--to", required=True)
    move.add_argument("--role", required=True)
    move.add_argument("--summary", required=True)
    move.add_argument("--evidence", action="append", default=[])
    sub.add_parser("workflow")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        workflow = load_json(WORKFLOW_FILE)
        if args.command == "workflow":
            print(json.dumps(workflow, indent=2, sort_keys=True))
            return 0
        if args.command == "new":
            item = create(args)
        else:
            item = transition(load_json(args.file), args, workflow)
        args.file.parent.mkdir(parents=True, exist_ok=True)
        args.file.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{item['id']}: {item['status']}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"work item error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
