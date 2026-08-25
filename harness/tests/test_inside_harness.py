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
        self.assertTrue((self.repo / ".agents/skills").is_symlink())
        self.assertTrue((self.repo / ".claude/skills").is_symlink())
        self.assertTrue((self.repo / ".inside-harness/skills/REGISTRY.md").is_file())
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
        lifecycle_script = self.repo / ".github/scripts/close-completed-parents.sh"
        self.assertEqual(
            lifecycle_script.read_text(),
            (
                WORKSPACE
                / "harness/packages/inside-engineering/github/close-completed-parents.sh"
            ).read_text(),
        )
        self.assertTrue(lifecycle_script.stat().st_mode & 0o111)

    def test_lifecycle_authority_is_discoverable_from_owning_skills(self) -> None:
        package = WORKSPACE / "harness/packages/inside-engineering"
        workflow = (package / "WORKFLOW.md").read_text()
        implementation = (package / "skills/implement/SKILL.md").read_text()
        adr_format = (package / "skills/domain-modeling/ADR-FORMAT.md").read_text()

        for section in ("Review closure", "Architecture fitness", "Pruning"):
            self.assertEqual(workflow.count(f"### {section}"), 1)
            self.assertIn(f"`{section}`", implementation)
        self.assertIn("repository-root `WORKFLOW.md`", implementation)
        self.assertIn("`Pruning`", adr_format)
        self.assertIn("repository-root `WORKFLOW.md`", adr_format)

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
        target = self.repo / ".inside-harness/skills/implement/SKILL.md"
        target.write_text(target.read_text() + "\ndrift\n")
        result = self.run_cli("diff", str(self.repo), expected=1)
        self.assertIn("snapshot/implement/M SKILL.md", result.stdout)
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

    def test_health_requires_coding_standards_to_be_discoverable(self) -> None:
        self.install()
        (self.repo / "CODING_STANDARDS.md").write_text("# Coding Standards\n")

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("coding-standards context pointer", result.stderr)

        agents = self.repo / "AGENTS.md"
        agents.write_text(agents.read_text() + "\nSee `CODING_STANDARDS.md`.\n")
        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("coding-standards context pointer", result.stderr)

        agents.write_text(
            agents.read_text()
            + "\nFor coding and review rules, read `CODING_STANDARDS.md`.\n"
        )
        self.run_cli("health", str(self.repo))

    def test_health_rejects_a_coding_standards_directory(self) -> None:
        self.install()
        (self.repo / "CODING_STANDARDS.md").mkdir()

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("Coding standards path is not a file", result.stderr)

    def test_health_requires_an_explicit_adr_lifecycle_status(self) -> None:
        self.install()
        adr = self.repo / "docs/adr/0001-runtime-shape.md"
        adr.parent.mkdir(parents=True)
        adr.write_text("# Runtime shape\n\nUse one runtime.\n")

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("ADR must declare a lifecycle status", result.stderr)

    def test_health_requires_a_superseding_adr_to_exist(self) -> None:
        self.install()
        adr_root = self.repo / "docs/adr"
        adr_root.mkdir(parents=True)
        (adr_root / "0001-old-shape.md").write_text(
            "---\nstatus: superseded by ADR-0002\n---\n\n# Old shape\n"
        )

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("references missing ADR-0002", result.stderr)

        (adr_root / "0002-new-shape.md").write_text(
            "---\nstatus: accepted\n---\n\n# New shape\n"
        )
        self.run_cli("health", str(self.repo))

    def test_health_rejects_duplicate_adr_numbers(self) -> None:
        self.install()
        adr_root = self.repo / "docs/adr"
        adr_root.mkdir(parents=True)
        (adr_root / "0001-first-decision.md").write_text(
            "---\nstatus: accepted\n---\n\n# First decision\n"
        )
        (adr_root / "0001-second-decision.md").write_text(
            "---\nstatus: accepted\n---\n\n# Second decision\n"
        )

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("Duplicate ADR-0001", result.stderr)

    def test_health_requires_supersession_to_point_forward(self) -> None:
        self.install()
        adr_root = self.repo / "docs/adr"
        adr_root.mkdir(parents=True)
        (adr_root / "0001-original-decision.md").write_text(
            "---\nstatus: accepted\n---\n\n# Original decision\n"
        )
        (adr_root / "0002-newer-decision.md").write_text(
            "---\nstatus: superseded by ADR-0001\n---\n\n# Newer decision\n"
        )

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("must be superseded by a later ADR number", result.stderr)

    def test_update_allows_a_new_manifest_skill_in_an_uncommitted_install(self) -> None:
        self.install()
        name = "frontend-design"
        state_path = self.repo / ".inside-harness/product-harness.json"
        state = json.loads(state_path.read_text())
        state["managedSkills"].remove(name)
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        shutil.rmtree(self.repo / ".inside-harness/skills" / name)

        self.run_cli("update", str(self.repo))
        self.run_cli("health", str(self.repo))

    def test_update_refuses_to_restore_a_deleted_managed_skill_in_a_dirty_install(self) -> None:
        self.install()
        shutil.rmtree(self.repo / ".inside-harness/skills/implement")
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
        self.assertEqual(
            (self.repo / ".agents/skills").resolve(),
            (self.repo / ".claude/skills").resolve(),
        )

    def test_registry_folds_multiline_skill_descriptions(self) -> None:
        self.install()
        registry = (self.repo / ".inside-harness/skills/REGISTRY.md").read_text()
        self.assertIn(
            "Search tool for modern web development best practices. MANDATORY:",
            registry,
        )
        self.assertNotIn(
            "| `modern-web-guidance` | `.inside-harness/skills/modern-web-guidance` | \\| |",
            registry,
        )

    def test_registry_supports_yaml_block_scalar_indicators(self) -> None:
        skill = self.repo / ".agents/skills/local-folded"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: local-folded\n"
            "description: >-\n"
            "  First line.\n"
            "  Second line.\n"
            "---\n"
        )
        self.install()
        registry = (self.repo / ".inside-harness/skills/REGISTRY.md").read_text()
        self.assertIn("First line. Second line.", registry)

    def test_migration_refuses_unexpected_entries_before_deleting_legacy_roots(self) -> None:
        unexpected = self.repo / ".agents/skills/README.md"
        unexpected.parent.mkdir(parents=True)
        unexpected.write_text("keep me\n")
        self.run_cli("install", str(self.repo), expected=2)
        self.assertEqual(unexpected.read_text(), "keep me\n")
        self.assertFalse((self.repo / ".inside-harness/skills/REGISTRY.md").exists())


if __name__ == "__main__":
    unittest.main()
