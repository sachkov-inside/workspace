from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
CLI = WORKSPACE / "harness/bin/inside-harness"
MANIFEST = json.loads((WORKSPACE / "harness/packages/inside-engineering/manifest.json").read_text())


class HarnessCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="inside-harness-test-")
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(CLI), *args],
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def install(self, *extra: str) -> None:
        self.run_cli("install", str(self.repo), *extra)

    def test_clean_install_health_and_idempotence(self) -> None:
        self.install()
        self.run_cli("health", str(self.repo))
        before = subprocess.run(
            ["git", "-C", str(self.repo), "status", "--porcelain"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout
        self.install()
        after = subprocess.run(
            ["git", "-C", str(self.repo), "status", "--porcelain"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout
        self.assertEqual(before, after)
        self.assertTrue((self.repo / ".agents/skills/implement/SKILL.md").is_file())
        self.assertTrue((self.repo / ".claude/skills/implement/SKILL.md").is_file())
        self.assertEqual(
            (self.repo / "WORKFLOW.md").read_text(),
            (WORKSPACE / "harness/packages/inside-engineering/WORKFLOW.md").read_text(),
        )
        self.assertEqual(
            (self.repo / "docs/agents/triage-labels.md").read_text(),
            (
                WORKSPACE
                / "harness/packages/inside-engineering/docs/agents/triage-labels.md"
            ).read_text(),
        )

    def test_existing_skill_requires_explicit_adoption(self) -> None:
        skill = self.repo / ".agents/skills/implement"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("local\n")
        self.run_cli("install", str(self.repo), expected=2)
        self.run_cli("install", str(self.repo), "--adopt-existing")
        self.assertIn("name: implement", (skill / "SKILL.md").read_text())

    def test_repo_specific_skill_is_preserved(self) -> None:
        local = self.repo / ".agents/skills/local-only"
        local.mkdir(parents=True)
        (local / "SKILL.md").write_text("---\nname: local-only\ndescription: local\n---\n")
        self.install()
        self.run_cli("update", str(self.repo))
        self.assertTrue((local / "SKILL.md").is_file())

    def test_health_and_diff_detect_drift(self) -> None:
        self.install()
        target = self.repo / ".agents/skills/implement/SKILL.md"
        target.write_text(target.read_text() + "\ndrift\n")
        result = self.run_cli("diff", str(self.repo), expected=1)
        self.assertIn("portable/implement/M SKILL.md", result.stdout)
        self.run_cli("health", str(self.repo), expected=2)
        self.run_cli("update", str(self.repo), expected=2)

    def test_health_and_diff_detect_managed_workflow_drift(self) -> None:
        self.install()
        workflow = self.repo / "WORKFLOW.md"
        workflow.write_text(workflow.read_text() + "\ndrift\n")
        result = self.run_cli("diff", str(self.repo), expected=1)
        self.assertIn("file/WORKFLOW.md/M", result.stdout)
        self.run_cli("health", str(self.repo), expected=2)
        self.run_cli("update", str(self.repo), expected=2)

    def test_diff_detects_managed_entrypoint_drift(self) -> None:
        self.install()
        agents = self.repo / "AGENTS.md"
        agents.write_text(agents.read_text().replace("owner-controlled merge", "merge"))
        result = self.run_cli("diff", str(self.repo), expected=1)
        self.assertIn("entrypoint/AGENTS.md/M", result.stdout)

    def test_update_allows_a_new_manifest_skill_in_an_uncommitted_install(self) -> None:
        self.install()
        name = "frontend-design"
        state_path = self.repo / ".inside-harness/product-harness.json"
        state = json.loads(state_path.read_text())
        state["managedSkills"].remove(name)
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        shutil.rmtree(self.repo / ".agents/skills" / name)
        shutil.rmtree(self.repo / ".claude/skills" / name)

        self.run_cli("update", str(self.repo))
        self.run_cli("health", str(self.repo))

    def test_update_refuses_to_restore_a_deleted_managed_skill_in_a_dirty_install(self) -> None:
        self.install()
        shutil.rmtree(self.repo / ".agents/skills/implement")
        self.run_cli("update", str(self.repo), expected=2)

    def test_unrelated_claude_settings_are_untouched(self) -> None:
        settings = self.repo / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"permissions": {"allow": ["Read"]}}))
        self.install()
        value = json.loads(settings.read_text())
        self.assertEqual(value, {"permissions": {"allow": ["Read"]}})

    def test_all_manifest_skills_are_installed_once_per_runtime_route(self) -> None:
        self.install()
        portable = {path.name for path in (self.repo / ".agents/skills").iterdir() if path.is_dir()}
        claude = {path.name for path in (self.repo / ".claude/skills").iterdir() if path.is_dir()}
        self.assertEqual(portable, set(MANIFEST["skills"]))
        self.assertEqual(claude, set(MANIFEST["skills"]))


if __name__ == "__main__":
    unittest.main()
