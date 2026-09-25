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
log = os.environ["FAKE_GH_LOG"]
with open(log, "a") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["pr", "list"]:
    print(os.environ.get("FAKE_GH_OPEN_PRS", "[]"))
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
        self.remotes.mkdir()
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

    def consumer(self, name: str, *, behind: bool) -> Path:
        work = self.root / f"{name}-work"
        work.mkdir()
        git("init", "-q", "-b", "main", str(work))
        subprocess.run([str(CLI), "install", str(work)], check=True, capture_output=True)
        if behind:
            (work / "WORKFLOW.md").unlink()
        git("add", "--all", cwd=work)
        git("commit", "-qm", "consumer", cwd=work)
        remote = self.remotes / f"{name}.git"
        git("clone", "-q", "--bare", str(work), str(remote))
        return remote

    def rollout(self, *targets: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        targets_file = self.root / "targets.json"
        targets_file.write_text(json.dumps({"schemaVersion": 1, "targets": list(targets)}))
        result = subprocess.run(
            [
                str(ROLLOUT),
                "--targets", str(targets_file),
                "--remote-template", f"{self.remotes}/{{name}}.git",
            ],
            env=self.env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def gh_calls(self) -> list[list[str]]:
        if not self.gh_log.exists():
            return []
        return [json.loads(line) for line in self.gh_log.read_text().splitlines()]

    def test_behind_consumer_gets_branch_and_pull_request(self) -> None:
        remote = self.consumer("platform", behind=True)

        result = self.rollout("example/platform")

        self.assertIn("example/platform: opened https://github.com/example/pull/1", result.stdout)
        self.assertIn("WORKFLOW.md", git("show", "--name-only", "--format=", BRANCH, cwd=remote))
        creates = [call for call in self.gh_calls() if call[:2] == ["pr", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertIn(BRANCH, creates[0])

    def test_current_consumer_gets_nothing(self) -> None:
        remote = self.consumer("telegram", behind=False)

        result = self.rollout("example/telegram")

        self.assertIn("example/telegram: current", result.stdout)
        self.assertEqual(git("branch", "--list", BRANCH, cwd=remote).strip(), "")
        self.assertEqual(self.gh_calls(), [])

    def test_open_pull_request_is_updated_not_duplicated(self) -> None:
        self.consumer("cases", behind=True)
        self.env["FAKE_GH_OPEN_PRS"] = '[{"number": 7}]'

        result = self.rollout("example/cases")

        self.assertIn("example/cases: updated #7", result.stdout)
        self.assertFalse(any(call[:2] == ["pr", "create"] for call in self.gh_calls()))

    def test_missing_token_blocks_default_remote(self) -> None:
        targets_file = self.root / "targets.json"
        targets_file.write_text(json.dumps({"schemaVersion": 1, "targets": ["example/platform"]}))

        result = subprocess.run(
            [str(ROLLOUT), "--targets", str(targets_file)], env=self.env, text=True, capture_output=True
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("GH_TOKEN", result.stdout)
        self.assertEqual(self.gh_calls(), [])

    def test_one_failed_target_does_not_stop_the_others(self) -> None:
        self.consumer("platform", behind=True)

        result = self.rollout("example/missing", "example/platform", expected=1)

        self.assertIn("example/missing: failed", result.stdout)
        self.assertIn("example/platform: opened", result.stdout)


if __name__ == "__main__":
    unittest.main()
