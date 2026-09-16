#!/usr/bin/env python3
"""Install the portable governance plugin into a project for one AI host."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ENGINE_SOURCE = PLUGIN_ROOT / "scripts" / "governance_hook.py"
WORK_ITEM_SOURCE = PLUGIN_ROOT / "scripts" / "work_item.py"
WORKFLOW_SOURCE = PLUGIN_ROOT / "workflow" / "role-workflow.json"
POLICY_SOURCE = PLUGIN_ROOT / "examples" / "policy.json"
INSTALL_DIR = Path(".ai-governance") / "plugin"
ENGINE_TARGET = INSTALL_DIR / "governance_hook.py"
WORK_ITEM_TARGET = INSTALL_DIR / "work_item.py"
WORKFLOW_TARGET = INSTALL_DIR / "workflow" / "role-workflow.json"
MARKER = ".ai-governance/plugin/governance_hook.py"


def command(provider: str, event: str) -> str:
    return f'python3 "{ENGINE_TARGET.as_posix()}" hook --provider {provider} --event {event}'


def handler(provider: str, event: str, *, gemini: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "command",
        "command": command(provider, event),
    }
    if gemini:
        result.update({"name": f"ai-change-governance-{event}", "timeout": 30000})
    else:
        result.update({"timeout": 30, "statusMessage": "Checking AI change governance"})
    return result


def hook_groups(tool: str) -> dict[str, list[dict[str, Any]]]:
    if tool == "gemini":
        return {
            "BeforeTool": [{"matcher": "write_file|replace|run_shell_command", "hooks": [handler("gemini", "pre", gemini=True)]}],
            "AfterTool": [{"matcher": "write_file|replace|run_shell_command", "hooks": [handler("gemini", "post", gemini=True)]}],
        }
    provider = "claude" if tool == "claude" else "codex"
    matcher = "Edit|Write|MultiEdit|Bash" if tool == "claude" else "apply_patch|Edit|Write|MultiEdit|Bash|Shell|exec_command"
    return {
        "PreToolUse": [{"matcher": matcher, "hooks": [handler(provider, "pre")]}],
        "PostToolUse": [{"matcher": matcher, "hooks": [handler(provider, "post")]}],
    }


def config_path(tool: str) -> Path:
    return {
        "codex": Path(".codex/hooks.json"),
        "claude": Path(".claude/settings.json"),
        "gemini": Path(".gemini/settings.json"),
        "generic": Path(".ai-governance/hooks.json"),
    }[tool]


def skills_path(tool: str) -> Path:
    return {
        "codex": Path(".codex/skills"),
        "claude": Path(".claude/skills"),
        "gemini": Path(".gemini/skills"),
        "generic": Path(".ai-governance/skills"),
    }[tool]


def contains_our_hook(group: Any) -> bool:
    if not isinstance(group, dict):
        return False
    return any(
        isinstance(item, dict) and MARKER in str(item.get("command", ""))
        for item in group.get("hooks", [])
    )


def merged_config(existing: dict[str, Any], tool: str) -> dict[str, Any]:
    if tool == "generic":
        return {
            "schema_version": 1,
            "protocol": "stdin-json/stdout-json",
            "pre": command("generic", "pre"),
            "post": command("generic", "post"),
        }
    result = dict(existing)
    hooks = dict(result.get("hooks", {}))
    for event, additions in hook_groups(tool).items():
        retained = [group for group in hooks.get(event, []) if not contains_our_hook(group)]
        hooks[event] = retained + additions
    result["hooks"] = hooks
    return result


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def install(project: Path, tool: str, dry_run: bool) -> list[Path]:
    project = project.resolve()
    if not project.is_dir():
        raise ValueError(f"project directory does not exist: {project}")
    relative_config = config_path(tool)
    target_config = project / relative_config
    existing = read_json(target_config)
    rendered = json.dumps(merged_config(existing, tool), indent=2, sort_keys=True) + "\n"
    relative_skills = skills_path(tool)
    changed = [ENGINE_TARGET, WORK_ITEM_TARGET, WORKFLOW_TARGET, relative_skills, relative_config]
    policy_target = project / ".ai-governance.json"
    if not policy_target.exists():
        changed.append(Path(".ai-governance.json"))
    if dry_run:
        return changed
    engine_target = project / ENGINE_TARGET
    engine_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ENGINE_SOURCE, engine_target)
    shutil.copyfile(WORK_ITEM_SOURCE, project / WORK_ITEM_TARGET)
    workflow_target = project / WORKFLOW_TARGET
    workflow_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WORKFLOW_SOURCE, workflow_target)
    for skill in PLUGIN_ROOT.joinpath("skills").iterdir():
        if skill.is_dir() and (skill / "SKILL.md").is_file():
            shutil.copytree(skill, project / relative_skills / skill.name, dirs_exist_ok=True)
    shared_references = PLUGIN_ROOT / "skills" / "references"
    if shared_references.is_dir():
        shutil.copytree(shared_references, project / relative_skills / "references", dirs_exist_ok=True)
    if not policy_target.exists():
        shutil.copyfile(POLICY_SOURCE, policy_target)
    target_config.parent.mkdir(parents=True, exist_ok=True)
    target_config.write_text(rendered, encoding="utf-8")
    return changed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--tool", required=True, choices=("codex", "claude", "gemini", "generic"))
    result.add_argument("--project", required=True, type=Path)
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        changed = install(args.project, args.tool, args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"install failed: {exc}")
        return 1
    verb = "Would install" if args.dry_run else "Installed"
    print(f"{verb} ai-change-governance for {args.tool}:")
    for path in changed:
        print(f"- {path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
