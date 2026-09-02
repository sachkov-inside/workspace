from __future__ import annotations

import hashlib
import json
import runpy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
CLI = WORKSPACE / "harness/bin/inside-harness"
MANIFEST = json.loads((WORKSPACE / "harness/packages/inside-engineering/manifest.json").read_text())
HARNESS = runpy.run_path(str(CLI))
HarnessError = HARNESS["HarnessError"]
load_manifest = HARNESS["load_manifest"]
validated_skill_metadata = HARNESS["validated_skill_metadata"]


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
        state = json.loads((self.repo / ".inside-harness/product-harness.json").read_text())
        self.assertEqual(state["profile"], MANIFEST["defaultProfile"])
        self.assertEqual(state["schemaVersion"], 3)

    def test_lifecycle_authority_is_discoverable_from_owning_skills(self) -> None:
        package = WORKSPACE / "harness/packages/inside-engineering"
        workflow = (package / "WORKFLOW.md").read_text()
        implementation = (package / "skills/implement/SKILL.md").read_text()
        adr_format = (package / "skills/domain-modeling/ADR-FORMAT.md").read_text()

        for section in (
            "Review closure",
            "Pull request CI closure",
            "Architecture fitness",
            "Pruning",
        ):
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
        agents.write_text(agents.read_text().replace("shared delivery rules", "delivery rules"))
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
        name = "domain-modeling"
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
        expected = set(MANIFEST["skillProfiles"][MANIFEST["defaultProfile"]])
        self.assertEqual(portable, expected)
        self.assertEqual(claude, expected)
        self.assertEqual(
            (self.repo / ".agents/skills").resolve(),
            (self.repo / ".claude/skills").resolve(),
        )

    def test_registry_folds_multiline_skill_descriptions(self) -> None:
        self.install("--profile", "frontend")
        registry = (self.repo / ".inside-harness/skills/REGISTRY.md").read_text()
        self.assertIn(
            "Search tool for modern web development best practices. MANDATORY:",
            registry,
        )
        self.assertNotIn(
            "| `modern-web-guidance` | Model | `.inside-harness/skills/modern-web-guidance` | \\| |",
            registry,
        )

    def test_registry_preserves_user_only_invocation(self) -> None:
        self.install()
        registry = (self.repo / ".inside-harness/skills/REGISTRY.md").read_text()
        self.assertIn("| `ask-matt` | User |", registry)
        self.assertIn("| `code-review` | Model |", registry)
        self.assertIn("route by intent only to `Model` skills", registry)

    def test_profile_switch_removes_only_previously_managed_skills(self) -> None:
        self.install("--profile", "frontend")
        local = self.repo / ".inside-harness/skills/local-only"
        local.mkdir()
        (local / "SKILL.md").write_text(
            "---\nname: local-only\ndescription: Local only.\n---\n"
        )
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "-c",
                "user.name=Harness Test",
                "-c",
                "user.email=harness@example.invalid",
                "commit",
                "-qm",
                "install frontend profile",
            ],
            check=True,
        )

        self.run_cli("update", str(self.repo), "--profile", "core")

        self.assertFalse((self.repo / ".inside-harness/skills/impeccable").exists())
        self.assertTrue(local.is_dir())
        self.run_cli("health", str(self.repo))

    def test_profile_migration_requires_an_explicit_selection_once(self) -> None:
        self.install()
        state_path = self.repo / ".inside-harness/product-harness.json"
        state = json.loads(state_path.read_text())
        state["schemaVersion"] = 2
        state.pop("profile")
        state_path.write_text(json.dumps(state, indent=2) + "\n")

        result = self.run_cli("update", str(self.repo), expected=2)
        self.assertIn("predates skill profiles", result.stderr)

        self.run_cli("update", str(self.repo), "--profile", "core")
        self.run_cli("health", str(self.repo))

    def test_install_rejects_an_unknown_profile(self) -> None:
        result = self.run_cli(
            "install", str(self.repo), "--profile", "unknown", expected=2
        )
        self.assertIn("Unknown skill profile", result.stderr)

    def test_manifest_rejects_invalid_profile_definitions(self) -> None:
        package = Path(self.temp.name) / "package"
        package.mkdir()
        cases = (
            (
                "invalid default",
                {
                    "schemaVersion": 1,
                    "name": "inside-engineering",
                    "version": "test",
                    "skills": ["one"],
                    "defaultProfile": "missing",
                    "skillProfiles": {"core": ["one"]},
                },
                "valid defaultProfile",
            ),
            (
                "empty profile name",
                {
                    "schemaVersion": 1,
                    "name": "inside-engineering",
                    "version": "test",
                    "skills": ["one"],
                    "defaultProfile": "",
                    "skillProfiles": {"": ["one"]},
                },
                "profile names",
            ),
            (
                "unknown profile skill",
                {
                    "schemaVersion": 1,
                    "name": "inside-engineering",
                    "version": "test",
                    "skills": ["one"],
                    "defaultProfile": "core",
                    "skillProfiles": {"core": ["missing"]},
                },
                "Invalid skill profile",
            ),
            (
                "unused package skill",
                {
                    "schemaVersion": 1,
                    "name": "inside-engineering",
                    "version": "test",
                    "skills": ["one", "two"],
                    "defaultProfile": "core",
                    "skillProfiles": {"core": ["one"]},
                },
                "Every package skill",
            ),
        )
        for name, manifest, message in cases:
            with self.subTest(name=name):
                (package / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(HarnessError, message):
                    load_manifest(package)

    def test_skill_metadata_rejects_invalid_model_invocation_flag(self) -> None:
        skill = Path(self.temp.name) / "invalid-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: invalid-skill\n"
            "description: Invalid test skill.\n"
            "disable-model-invocation: sometimes\n"
            "---\n"
        )

        with self.assertRaisesRegex(HarnessError, "disable-model-invocation"):
            validated_skill_metadata(skill)

    def test_update_rejects_an_invalid_obsolete_skill_target(self) -> None:
        self.install()
        state_path = self.repo / ".inside-harness/product-harness.json"
        state = json.loads(state_path.read_text())
        state["managedSkills"].append("obsolete")
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        obsolete = self.repo / ".inside-harness/skills/obsolete"
        obsolete.write_text("not a directory\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "-c",
                "user.name=Harness Test",
                "-c",
                "user.email=harness@example.invalid",
                "commit",
                "-qm",
                "record invalid obsolete target",
            ],
            check=True,
        )

        result = self.run_cli("update", str(self.repo), expected=2)
        self.assertIn("invalid obsolete skill path", result.stderr)

    def test_health_rejects_broken_agent_document_pointer(self) -> None:
        self.install()
        agents = self.repo / "AGENTS.md"
        agents.write_text(agents.read_text() + "\n[Missing](docs/agents/missing.md)\n")

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("local pointer does not resolve", result.stderr)

    def test_health_rejects_agent_document_pointers_outside_repository(self) -> None:
        self.install()
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("# Outside\n")
        agents = self.repo / "AGENTS.md"
        original = agents.read_text()

        agents.write_text(original + "\n[Outside](../outside.md)\n")
        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("pointer escapes repository", result.stderr)

        linked = self.repo / "docs/outside.md"
        linked.parent.mkdir(exist_ok=True)
        linked.symlink_to(outside)
        agents.write_text(original + "\n[Outside](docs/outside.md)\n")
        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("pointer escapes repository", result.stderr)

    def test_health_rejects_machine_local_path_in_direct_reference(self) -> None:
        self.install()
        product = self.repo / "product/README.md"
        product.parent.mkdir()
        product.write_text("Canonical source: `/Users/example/private/product.md`.\n")
        agents = self.repo / "AGENTS.md"
        agents.write_text(agents.read_text() + "\n[Product](product/README.md)\n")

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("machine-local path is not portable", result.stderr)

    def test_health_requires_native_integration_inventory_and_hash(self) -> None:
        self.install()
        config = self.repo / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text("[mcp_servers.example]\ncommand = \"example\"\n")

        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("Invalid integration inventory", result.stderr)

        inventory = self.repo / ".inside-harness/integrations.json"
        inventory.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "integrations": [
                        {
                            "path": ".codex/config.toml",
                            "sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
                            "runtimes": ["codex"],
                            "verification": "example --help",
                            "secretEnvironmentVariables": [],
                        }
                    ],
                },
                indent=2,
            )
            + "\n"
        )
        self.run_cli("health", str(self.repo))

        inventory_value = json.loads(inventory.read_text())
        inventory_value["integrations"][0]["runtimes"] = ["claude"]
        inventory.write_text(json.dumps(inventory_value, indent=2) + "\n")
        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("Integration runtimes differ", result.stderr)

        inventory_value["integrations"][0]["runtimes"] = ["codex"]
        inventory.write_text(json.dumps(inventory_value, indent=2) + "\n")
        config.write_text(config.read_text() + "startup_timeout_sec = 10\n")
        result = self.run_cli("health", str(self.repo), expected=2)
        self.assertIn("Integration hash differs", result.stderr)

    def test_health_rejects_invalid_integration_inventory_entries(self) -> None:
        self.install()
        config = self.repo / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text("[mcp_servers.example]\ncommand = \"example\"\n")
        inventory = self.repo / ".inside-harness/integrations.json"
        valid_entry = {
            "path": ".codex/config.toml",
            "sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
            "runtimes": ["codex"],
            "verification": "example --help",
            "secretEnvironmentVariables": [],
        }

        cases = (
            ("non-object", ["invalid"], "Invalid integration inventory entry"),
            (
                "unsafe path",
                [{**valid_entry, "path": "../config.toml"}],
                "Unsafe integration path",
            ),
            (
                "duplicate path",
                [valid_entry, valid_entry],
                "Duplicate integration inventory path",
            ),
            ("missing entry", [], "missing=\\['.codex/config.toml'\\]"),
            (
                "extra entry",
                [valid_entry, {**valid_entry, "path": "custom/config.toml"}],
                "extra=\\['custom/config.toml'\\]",
            ),
            (
                "empty runtimes",
                [{**valid_entry, "runtimes": []}],
                "runtimes must be a non-empty list",
            ),
            (
                "empty verification",
                [{**valid_entry, "verification": "  "}],
                "verification is required",
            ),
            (
                "invalid secret name",
                [{**valid_entry, "secretEnvironmentVariables": ["not-secret"]}],
                "Invalid secret environment-variable names",
            ),
        )

        for name, entries, message in cases:
            with self.subTest(name=name):
                inventory.write_text(
                    json.dumps(
                        {"schemaVersion": 1, "integrations": entries}, indent=2
                    )
                    + "\n"
                )
                result = self.run_cli("health", str(self.repo), expected=2)
                self.assertRegex(result.stderr, message)

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
