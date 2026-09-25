from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
ROLLOUT = WORKSPACE / "harness/bin/harness-rollout"
CLI = WORKSPACE / "harness/bin/inside-harness"
VERSION = json.loads((WORKSPACE / "harness/packages/inside-engineering/manifest.json").read_text())["version"]
BRANCH = f"chore/harness-{VERSION}"

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_GH_LOG"], "a") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["pr", "list"]:
    print(os.environ.get("FAKE_GH_PULL_REQUESTS", "[]"))
elif sys.argv[1:3] == ["pr", "create"]:
    print("https://github.com/example/pull/1")
"""


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    ).stdout


class HarnessRolloutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="harness-rollout-test-")
        self.root = Path(self.temp.name)
        self.remotes = self.root / "remotes"
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.gh_log = self.root / "gh.log"
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_LOG": str(self.gh_log),
        }
        self.env.pop("GH_TOKEN", None)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def consumer(self, repository: str, *, behind: bool) -> Path:
        work = self.root / "work" / repository
        work.mkdir(parents=True)
        git("init", "-q", "-b", "main", str(work))
        subprocess.run([str(CLI), "install", str(work)], check=True, capture_output=True)
        if behind:
            (work / "WORKFLOW.md").unlink()
        git("add", "--all", cwd=work)
        git("commit", "-qm", "consumer", cwd=work)
        remote = self.remotes / f"{repository}.git"
        remote.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "-q", "--bare", str(work), str(remote))
        return remote

    def push_rollout_branch(self, remote: Path, *, updated: bool) -> None:
        """Leave a rollout branch on the remote, as an earlier run would have."""
        clone = self.root / "earlier-run"
        git("clone", "-q", str(remote), str(clone))
        git("checkout", "-q", "-b", BRANCH, cwd=clone)
        if updated:
            subprocess.run([str(CLI), "update", str(clone)], check=True, capture_output=True)
            git("add", "--all", cwd=clone)
        git("commit", "-q", "--allow-empty", "-m", "earlier rollout", cwd=clone)
        git("push", "-q", "origin", BRANCH, cwd=clone)

    def advance_main(self, remote: Path) -> None:
        clone = self.root / "later-work"
        git("clone", "-q", str(remote), str(clone))
        (clone / "NOTES.md").write_text("Unrelated work on main.\n")
        git("add", "NOTES.md", cwd=clone)
        git("commit", "-qm", "main moved", cwd=clone)
        git("push", "-q", "origin", "main", cwd=clone)

    def rollout(self, *targets: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        targets_file = self.root / "targets.json"
        targets_file.write_text(json.dumps({"schemaVersion": 1, "targets": list(targets)}))
        result = subprocess.run(
            [
                str(ROLLOUT),
                "--targets", str(targets_file),
                "--remote-template", f"{self.remotes}/{{repository}}.git",
            ],
            env=self.env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def gh_calls(self, *prefix: str) -> list[list[str]]:
        if not self.gh_log.exists():
            return []
        calls = [json.loads(line) for line in self.gh_log.read_text().splitlines()]
        return [call for call in calls if call[: len(prefix)] == list(prefix)]

    def test_behind_consumer_gets_branch_and_pull_request(self) -> None:
        remote = self.consumer("example/platform", behind=True)

        result = self.rollout("example/platform")

        self.assertIn("example/platform: opened https://github.com/example/pull/1", result.stdout)
        self.assertIn("WORKFLOW.md", git("show", "--name-only", "--format=", BRANCH, cwd=remote))
        creates = self.gh_calls("pr", "create")
        self.assertEqual(len(creates), 1)
        self.assertIn(BRANCH, creates[0])

    def test_current_consumer_gets_nothing(self) -> None:
        remote = self.consumer("example/telegram", behind=False)

        result = self.rollout("example/telegram")

        self.assertIn("example/telegram: current", result.stdout)
        self.assertEqual(git("branch", "--list", BRANCH, cwd=remote).strip(), "")
        self.assertEqual(self.gh_calls("pr", "create"), [])

    def test_leftover_branch_after_merge_counts_as_current(self) -> None:
        remote = self.consumer("example/cases", behind=False)
        self.push_rollout_branch(remote, updated=False)
        self.env["FAKE_GH_PULL_REQUESTS"] = '[{"number": 5, "state": "MERGED"}]'

        result = self.rollout("example/cases")

        self.assertIn("example/cases: current", result.stdout)
        self.assertEqual(self.gh_calls("pr", "create"), [])

    def test_leftover_branch_is_ignored_after_main_moves_on(self) -> None:
        remote = self.consumer("example/cases", behind=False)
        self.push_rollout_branch(remote, updated=False)
        self.advance_main(remote)
        self.env["FAKE_GH_PULL_REQUESTS"] = '[{"number": 5, "state": "MERGED"}]'

        result = self.rollout("example/cases")

        self.assertIn("example/cases: current", result.stdout)
        self.assertEqual(self.gh_calls("pr", "create"), [])

    def test_new_rollout_replaces_a_merged_leftover_branch(self) -> None:
        remote = self.consumer("example/cases", behind=True)
        self.push_rollout_branch(remote, updated=False)
        self.advance_main(remote)
        self.env["FAKE_GH_PULL_REQUESTS"] = '[{"number": 5, "state": "MERGED"}]'

        result = self.rollout("example/cases")

        self.assertIn("example/cases: opened", result.stdout)
        self.assertIn("main moved", git("log", "--format=%s", BRANCH, cwd=remote))
        self.assertNotIn("earlier rollout", git("log", "--format=%s", BRANCH, cwd=remote))

    def test_open_pull_request_gets_new_commit_not_a_duplicate(self) -> None:
        remote = self.consumer("example/cases", behind=True)
        self.push_rollout_branch(remote, updated=False)
        before = git("rev-parse", BRANCH, cwd=remote).strip()
        self.env["FAKE_GH_PULL_REQUESTS"] = '[{"number": 7, "state": "OPEN"}]'

        result = self.rollout("example/cases")

        self.assertIn("example/cases: updated #7", result.stdout)
        self.assertNotEqual(git("rev-parse", BRANCH, cwd=remote).strip(), before)
        self.assertEqual(self.gh_calls("pr", "create"), [])

    def test_rollout_closed_by_owner_is_not_reopened(self) -> None:
        remote = self.consumer("example/cases", behind=True)
        self.push_rollout_branch(remote, updated=True)
        before = git("rev-parse", BRANCH, cwd=remote).strip()
        self.env["FAKE_GH_PULL_REQUESTS"] = '[{"number": 8, "state": "CLOSED"}]'

        result = self.rollout("example/cases")

        self.assertIn("example/cases: declined #8", result.stdout)
        self.assertEqual(git("rev-parse", BRANCH, cwd=remote).strip(), before)
        self.assertEqual(self.gh_calls("pr", "create"), [])

    def test_missing_token_blocks_default_remote(self) -> None:
        targets_file = self.root / "targets.json"
        targets_file.write_text(json.dumps({"schemaVersion": 1, "targets": ["example/platform"]}))

        result = subprocess.run(
            [str(ROLLOUT), "--targets", str(targets_file)], env=self.env, text=True, capture_output=True
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("GH_TOKEN", result.stdout)
        self.assertEqual(self.gh_calls(), [])

    def test_invalid_targets_are_rejected_before_any_clone(self) -> None:
        targets_file = self.root / "targets.json"
        for content in (
            "not json",
            "[]",
            '{"schemaVersion": 2, "targets": []}',
            '{"schemaVersion": 1, "targets": ["platform"]}',
        ):
            with self.subTest(content=content):
                targets_file.write_text(content)
                result = subprocess.run(
                    [str(ROLLOUT), "--targets", str(targets_file), "--remote-template", "{repository}"],
                    env=self.env,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("Invalid rollout targets", result.stderr)
        self.assertEqual(self.gh_calls(), [])

    def test_one_failed_target_does_not_stop_the_others(self) -> None:
        self.consumer("example/platform", behind=True)

        result = self.rollout("example/missing", "example/platform", expected=1)

        self.assertIn("example/missing: failed", result.stdout)
        self.assertIn("example/platform: opened", result.stdout)

    def test_release_targets_are_the_active_consumers(self) -> None:
        targets = json.loads((WORKSPACE / "harness/rollout-targets.json").read_text())["targets"]

        self.assertEqual(
            targets,
            ["sachkov-inside/platform", "sachkov-inside/inside-telegram", "sachkov-inside/workshop-cases"],
        )
        self.assertNotIn("sachkov-inside/inside-landing", targets)


if __name__ == "__main__":
    unittest.main()
