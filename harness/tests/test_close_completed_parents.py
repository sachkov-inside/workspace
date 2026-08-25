from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
SCRIPT = (
    WORKSPACE
    / "harness/packages/inside-engineering/github/close-completed-parents.sh"
)


class CloseCompletedParentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="close-completed-parents-")
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.scenario = self.root / "scenario.json"
        self.log = self.root / "writes.jsonl"
        fake_gh = self.bin / "gh"
        fake_gh.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import re
                import sys

                args = sys.argv[1:]
                scenario = json.loads(open(os.environ["GH_FAKE_SCENARIO"]).read())

                def field(name):
                    prefix = name + "="
                    for argument in args:
                        if argument.startswith(prefix):
                            return argument[len(prefix):]
                    raise SystemExit("missing field " + name)

                if args[:2] == ["api", "graphql"]:
                    key = f"{field('owner')}/{field('repo')}#{field('number')}"
                    parent = scenario.get("parents", {}).get(key)
                    print(json.dumps({
                        "data": {
                            "repository": {
                                "issue": {
                                    "parent": parent,
                                }
                            }
                        }
                    }))
                    raise SystemExit(0)

                endpoints = [argument for argument in args if argument.startswith("repos/")]
                if not endpoints:
                    raise SystemExit("missing endpoint: " + repr(args))
                endpoint = endpoints[0]

                if "--paginate" in args and endpoint.endswith("sub_issues?per_page=100"):
                    match = re.fullmatch(r"repos/(.+)/issues/(\\d+)/sub_issues\\?per_page=100", endpoint)
                    key = f"{match.group(1)}#{match.group(2)}"
                    print(json.dumps([scenario.get("children", {}).get(key, [])]))
                    raise SystemExit(0)

                if "PATCH" in args:
                    with open(os.environ["GH_FAKE_LOG"], "a") as output:
                        output.write(json.dumps({"endpoint": endpoint, "args": args}) + "\\n")
                    raise SystemExit(0)

                raise SystemExit("unsupported gh invocation: " + repr(args))
                """
            )
        )
        fake_gh.chmod(0o755)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(self, scenario: dict) -> list[dict]:
        self.scenario.write_text(json.dumps(scenario))
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{self.bin}:{environment['PATH']}",
                "GH_FAKE_SCENARIO": str(self.scenario),
                "GH_FAKE_LOG": str(self.log),
                "REPOSITORY": "sachkov-inside/platform",
                "ISSUE_NUMBER": "89",
            }
        )
        result = subprocess.run(
            [str(SCRIPT)],
            text=True,
            capture_output=True,
            env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_no_parent_is_a_noop(self) -> None:
        self.assertEqual(self.run_script({"parents": {}}), [])

    def test_parent_without_children_stays_open(self) -> None:
        writes = self.run_script(
            {
                "parents": {
                    "sachkov-inside/platform#89": {
                        "number": 65,
                        "state": "OPEN",
                        "repository": {"nameWithOwner": "sachkov-inside/platform"},
                    }
                },
                "children": {"sachkov-inside/platform#65": []},
            }
        )
        self.assertEqual(writes, [])

    def test_open_child_keeps_parent_open(self) -> None:
        writes = self.run_script(
            {
                "parents": {
                    "sachkov-inside/platform#89": {
                        "number": 65,
                        "state": "OPEN",
                        "repository": {"nameWithOwner": "sachkov-inside/platform"},
                    }
                },
                "children": {
                    "sachkov-inside/platform#65": [
                        {"state": "closed", "state_reason": "completed"},
                        {"state": "open", "state_reason": None},
                    ]
                },
            }
        )
        self.assertEqual(writes, [])

    def test_not_planned_child_does_not_complete_parent(self) -> None:
        writes = self.run_script(
            {
                "parents": {
                    "sachkov-inside/platform#89": {
                        "number": 65,
                        "state": "OPEN",
                        "repository": {"nameWithOwner": "sachkov-inside/platform"},
                    }
                },
                "children": {
                    "sachkov-inside/platform#65": [
                        {"state": "closed", "state_reason": "not_planned"}
                    ]
                },
            }
        )
        self.assertEqual(writes, [])

    def test_completed_children_close_the_full_parent_chain(self) -> None:
        writes = self.run_script(
            {
                "parents": {
                    "sachkov-inside/platform#89": {
                        "number": 65,
                        "state": "OPEN",
                        "repository": {"nameWithOwner": "sachkov-inside/platform"},
                    },
                    "sachkov-inside/platform#65": {
                        "number": 81,
                        "state": "OPEN",
                        "repository": {"nameWithOwner": "sachkov-inside/workspace"},
                    },
                    "sachkov-inside/workspace#81": None,
                },
                "children": {
                    "sachkov-inside/platform#65": [
                        {"state": "closed", "state_reason": "completed"}
                    ],
                    "sachkov-inside/workspace#81": [
                        {"state": "closed", "state_reason": "completed"},
                        {"state": "closed", "state_reason": "completed"},
                    ],
                },
            }
        )
        self.assertEqual(
            [write["endpoint"] for write in writes],
            [
                "repos/sachkov-inside/platform/issues/65",
                "repos/sachkov-inside/workspace/issues/81",
            ],
        )
        for write in writes:
            self.assertIn("state=closed", write["args"])
            self.assertIn("state_reason=completed", write["args"])

    def test_already_closed_parent_is_not_patched_twice(self) -> None:
        writes = self.run_script(
            {
                "parents": {
                    "sachkov-inside/platform#89": {
                        "number": 65,
                        "state": "CLOSED",
                        "repository": {"nameWithOwner": "sachkov-inside/platform"},
                    },
                    "sachkov-inside/platform#65": None,
                },
                "children": {
                    "sachkov-inside/platform#65": [
                        {"state": "closed", "state_reason": "completed"}
                    ]
                },
            }
        )
        self.assertEqual(writes, [])


if __name__ == "__main__":
    unittest.main()
