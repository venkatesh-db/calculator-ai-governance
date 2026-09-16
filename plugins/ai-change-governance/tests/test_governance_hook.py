from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "governance_hook.py"


class GovernanceHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "cli.py").write_text("old = True\n")
        (self.root / "test_cli.py").write_text("test = True\n")
        (self.root / "AGENTS.md").write_text("# Ledger\n")
        (self.root / ".ai-governance.json").write_text(json.dumps({
            "version": 1,
            "test_first": {"protected_files": {"cli.py": {"watch": ["cli.py", "test*.py"], "valid_exit_codes": [0]}}},
            "audit": {"ledger_file": "AGENTS.md", "changelog_file": ".audit/events.jsonl", "suffixes": [".py"], "excluded_paths": []},
        }))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_hook(self, event: str, payload: dict, provider: str = "codex") -> dict:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "hook", "--provider", provider, "--event", event],
            cwd=self.root,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)

    def test_pre_hook_blocks_protected_file_without_evidence(self) -> None:
        result = self.run_hook("pre", {"cwd": str(self.root), "tool_name": "Edit", "tool_input": {"file_path": "cli.py"}})
        decision = result["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")

    def test_authorization_allows_unchanged_protected_file(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "authorize", "--file", "cli.py", "--requirement", "example", "--", sys.executable, "-c", "raise SystemExit(0)"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("authorized", completed.stdout)
        result = self.run_hook("pre", {"cwd": str(self.root), "tool_name": "Edit", "tool_input": {"file_path": "cli.py"}})
        self.assertEqual(result, {})

    def test_post_hook_records_hash_and_pending_ledger(self) -> None:
        result = self.run_hook("post", {"cwd": str(self.root), "tool_name": "Edit", "tool_input": {"file_path": "cli.py"}})
        self.assertIn("add fresh ledger entries", result["hookSpecificOutput"]["additionalContext"])
        event = json.loads((self.root / ".audit" / "events.jsonl").read_text().splitlines()[0])
        self.assertEqual(event["files"][0]["path"], "cli.py")
        self.assertEqual(len(event["files"][0]["sha256"]), 64)

    def test_gemini_denial_uses_native_shape(self) -> None:
        result = self.run_hook("pre", {"cwd": str(self.root), "tool_name": "write_file", "tool_input": {"file_path": "cli.py"}}, "gemini")
        self.assertEqual(result["decision"], "deny")

    def test_shell_mutation_of_protected_file_is_detected(self) -> None:
        result = self.run_hook("pre", {"cwd": str(self.root), "tool_name": "Bash", "tool_input": {"command": "sed -i 's/old/new/' cli.py"}})
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
