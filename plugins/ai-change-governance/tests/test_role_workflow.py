from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "scripts" / "work_item.py"


class RoleWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.item = Path(self.temp.name) / "WORK-1.json"
        subprocess.run([
            sys.executable, str(SCRIPT), "new", "--file", str(self.item),
            "--id", "WORK-1", "--title", "Example", "--outcome", "Observable outcome",
            "--criterion", "Behavior is verified",
        ], check=True, capture_output=True, text=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def move(self, status: str, role: str, *evidence: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(SCRIPT), "transition", "--file", str(self.item), "--to", status, "--role", role, "--summary", "handoff"]
        for value in evidence:
            command.extend(["--evidence", value])
        return subprocess.run(command, check=check, capture_output=True, text=True)

    def test_complete_role_sequence_records_handoffs(self) -> None:
        self.move("architecture-ready", "principal-architecture-role")
        self.move("implementation-complete", "sse-role", "tests passed")
        self.move("verified", "tester-role", "acceptance checks passed")
        self.move("accepted", "principal-architecture-role", "all criteria mapped")
        item = json.loads(self.item.read_text())
        self.assertEqual(item["status"], "accepted")
        self.assertEqual([entry["role"] for entry in item["handoffs"]], [
            "principal-architecture-role", "sse-role", "tester-role", "principal-architecture-role",
        ])

    def test_wrong_role_cannot_approve_transition(self) -> None:
        completed = self.move("architecture-ready", "sse-role", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("cannot transition", completed.stderr)

    def test_verification_requires_evidence(self) -> None:
        self.move("architecture-ready", "principal-architecture-role")
        self.move("implementation-complete", "sse-role", "implementation evidence")
        completed = self.move("verified", "tester-role", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires at least one", completed.stderr)

    def test_all_role_skills_are_packaged(self) -> None:
        for role in ("principal-architecture-role", "sse-role", "tester-role"):
            with self.subTest(role=role):
                self.assertTrue((PLUGIN / "skills" / role / "SKILL.md").is_file())
                self.assertTrue((PLUGIN / "skills" / role / "agents" / "openai.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
