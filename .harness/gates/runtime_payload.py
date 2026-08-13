#!/usr/bin/env python3
"""Normalize file paths from supported runtime hook payloads.

Claude and Kimi file tools expose ``file_path`` or ``path``. Codex exposes the
whole apply_patch document as ``tool_input.command``. Keeping this translation in
one helper prevents guidance and lint gates from silently disagreeing about which
files a tool call touches.
"""

from __future__ import annotations

import json
import re
import sys


PATCH_PATH = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$")
PATCH_MOVE = re.compile(r"^\*\*\* Move to: (.+)$")


def _append_unique(paths: list[str], value: object) -> None:
    if value is None:
        return
    path = str(value).strip()
    if path and path not in paths:
        paths.append(path)


def patch_paths(command: object) -> list[str]:
    if not isinstance(command, str):
        return []
    lines = command.splitlines()
    if lines.count("*** Begin Patch") != 1 or lines.count("*** End Patch") != 1:
        return []
    begin, end = lines.index("*** Begin Patch"), lines.index("*** End Patch")
    if begin >= end:
        return []
    paths: list[str] = []
    for line in lines[begin + 1 : end]:
        match = PATCH_PATH.match(line) or PATCH_MOVE.match(line)
        if match:
            _append_unique(paths, match.group(1))
    return paths


def target_paths(payload: dict) -> list[str]:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []

    paths: list[str] = []
    for key in ("file_path", "path", "notebook_path"):
        _append_unique(paths, tool_input.get(key))
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            _append_unique(paths, edit.get("file_path") or edit.get("path"))
    if payload.get("tool_name") == "apply_patch":
        for path in patch_paths(tool_input.get("command")):
            _append_unique(paths, path)
    return paths


def main() -> int:
    if sys.argv[1:] != ["paths"]:
        print("usage: runtime_payload.py paths", file=sys.stderr)
        return 2
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    for path in target_paths(payload):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
