from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / "scripts" / "install.py"


class PortableInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def install(self, tool: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSTALLER), "--tool", tool, "--project", str(self.project)],
            capture_output=True,
            text=True,
            check=True,
        )

    def test_each_supported_host_installs_from_same_package(self) -> None:
        expected = {
            "codex": self.project / ".codex" / "hooks.json",
            "claude": self.project / ".claude" / "settings.json",
            "gemini": self.project / ".gemini" / "settings.json",
            "generic": self.project / ".ai-governance" / "hooks.json",
        }
        for tool, config in expected.items():
            with self.subTest(tool=tool):
                self.install(tool)
                self.assertTrue(config.is_file())
        self.assertTrue((self.project / ".ai-governance" / "plugin" / "governance_hook.py").is_file())
        self.assertTrue((self.project / ".ai-governance" / "plugin" / "work_item.py").is_file())
        self.assertTrue((self.project / ".ai-governance.json").is_file())

    def test_role_skills_install_in_each_host_discovery_directory(self) -> None:
        expected = {"codex": ".codex/skills", "claude": ".claude/skills", "gemini": ".gemini/skills", "generic": ".ai-governance/skills"}
        for tool, directory in expected.items():
            with self.subTest(tool=tool):
                self.install(tool)
                for role in ("principal-architecture-role", "sse-role", "tester-role"):
                    self.assertTrue((self.project / directory / role / "SKILL.md").is_file())
                self.assertTrue((self.project / directory / "references" / "organizational-workflow.md").is_file())

    def test_install_preserves_existing_hooks_and_is_idempotent(self) -> None:
        config = self.project / ".codex" / "hooks.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{"type": "command", "command": "true"}]}]}}))
        self.install("codex")
        first = json.loads(config.read_text())
        self.install("codex")
        second = json.loads(config.read_text())
        self.assertEqual(first, second)
        self.assertEqual(len(second["hooks"]["PreToolUse"]), 2)
        self.assertEqual(second["hooks"]["PreToolUse"][0]["matcher"], "Read")

    def test_existing_policy_is_never_overwritten(self) -> None:
        policy = self.project / ".ai-governance.json"
        policy.write_text('{"version": 1, "team": "custom"}\n')
        self.install("gemini")
        self.assertEqual(json.loads(policy.read_text())["team"], "custom")


if __name__ == "__main__":
    unittest.main()
