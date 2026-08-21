from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "manage.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("platform_context_manage", SCRIPT)
assert SPEC and SPEC.loader
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


class ProductContextContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        for relative in (
            Path("product/platform-context/contract.json"),
            Path("product/platform-context/consumer.md"),
            Path("product/platform-context/verify_snapshot.py"),
            Path("product/platform-mvp-brief.md"),
        ):
            destination = self.workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(manage.REPO_ROOT / relative, destination)
        subprocess.run(["git", "init", "-q"], cwd=self.workspace, check=True)
        subprocess.run(["git", "add", "."], cwd=self.workspace, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=self.workspace,
            check=True,
        )

    def test_rendered_snapshot_verifies_and_matches_source(self) -> None:
        snapshot = self.root / "snapshot"

        manage.render(snapshot, self.workspace)

        result = subprocess.run(
            [sys.executable, snapshot / "verify.py"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        manifest = manage.verify(snapshot)
        manage.check(snapshot, self.workspace)
        self.assertEqual("1.0.0", manifest["version"])
        expected_revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(expected_revision, manifest["source"]["revision"])

    def test_verify_detects_local_payload_edit(self) -> None:
        snapshot = self.root / "snapshot"
        manage.render(snapshot, self.workspace)
        (snapshot / "platform-mvp-brief.md").write_text("changed\n", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, snapshot / "verify.py"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("checksum differs", result.stderr)

    def test_check_detects_source_edit_without_version_bump(self) -> None:
        snapshot = self.root / "snapshot"
        manage.render(snapshot, self.workspace)
        source = self.workspace / "product/platform-mvp-brief.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

        with self.assertRaisesRegex(manage.ContractError, "without a contract version bump"):
            manage.check(snapshot, self.workspace)

    def test_check_detects_explicit_new_version(self) -> None:
        snapshot = self.root / "snapshot"
        manage.render(snapshot, self.workspace)
        contract_path = self.workspace / manage.CONTRACT_PATH
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["version"] = "1.1.0"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")

        with self.assertRaisesRegex(manage.ContractError, "differs from Workspace contract 1.1.0"):
            manage.check(snapshot, self.workspace)

    def test_check_detects_false_provenance_revision(self) -> None:
        snapshot = self.root / "snapshot"
        manage.render(snapshot, self.workspace)
        manifest_path = snapshot / manage.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["source"]["revision"] = "f" * 40
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(manage.ContractError, "cannot resolve provenance"):
            manage.check(snapshot, self.workspace)

    def test_render_refuses_nonempty_output(self) -> None:
        snapshot = self.root / "snapshot"
        snapshot.mkdir()
        (snapshot / "keep.txt").write_text("keep\n", encoding="utf-8")

        with self.assertRaisesRegex(manage.ContractError, "must be empty"):
            manage.render(snapshot, self.workspace)

    def test_render_refuses_dirty_contract_input(self) -> None:
        source = self.workspace / "product/platform-mvp-brief.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

        with self.assertRaisesRegex(manage.ContractError, "differs from HEAD"):
            manage.render(self.root / "snapshot", self.workspace)


if __name__ == "__main__":
    unittest.main()
