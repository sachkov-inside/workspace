#!/usr/bin/env python3
"""Verify a self-contained Platform product-context snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


MANIFEST_NAME = "manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
REVISION = re.compile(r"^[0-9a-f]{40}$")


class SnapshotError(Exception):
    """A human-actionable snapshot validation error."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SnapshotError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise SnapshotError(f"{path} must contain a JSON object")
    return value


def relative_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise SnapshotError(f"{label} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SnapshotError(f"{label} must stay inside the snapshot: {value}")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_text(files: list[dict[str, str]]) -> str:
    return "".join(f'{entry["sha256"]}  {entry["path"]}\n' for entry in files)


def verify(snapshot: Path) -> dict[str, Any]:
    if not snapshot.is_dir() or snapshot.is_symlink():
        raise SnapshotError(f"snapshot directory does not exist or is a symlink: {snapshot}")
    manifest = read_json(snapshot / MANIFEST_NAME)
    required = {"schemaVersion", "name", "version", "source", "files"}
    if set(manifest) != required:
        raise SnapshotError(
            f"manifest keys must be exactly {sorted(required)}; got {sorted(manifest)}"
        )
    if manifest["schemaVersion"] != 1:
        raise SnapshotError("only manifest schemaVersion 1 is supported")
    if not isinstance(manifest["name"], str) or not manifest["name"]:
        raise SnapshotError("manifest name must be a non-empty string")
    if not isinstance(manifest["version"], str) or not SEMVER.fullmatch(manifest["version"]):
        raise SnapshotError("manifest version must be SemVer MAJOR.MINOR.PATCH")
    source = manifest["source"]
    if not isinstance(source, dict) or set(source) != {"repository", "revision"}:
        raise SnapshotError("manifest source must contain repository and revision")
    if not isinstance(source["repository"], str) or not source["repository"]:
        raise SnapshotError("manifest source.repository must be a non-empty string")
    if not isinstance(source["revision"], str) or not REVISION.fullmatch(source["revision"]):
        raise SnapshotError("manifest source.revision must be a full lowercase Git SHA")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        raise SnapshotError("manifest files must be a non-empty array")

    paths: set[Path] = set()
    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(manifest["files"]):
        if not isinstance(entry, dict) or set(entry) != {"source", "path", "sha256"}:
            raise SnapshotError(f"manifest files[{index}] has invalid keys")
        source_path = relative_path(entry["source"], f"manifest files[{index}].source")
        target = relative_path(entry["path"], f"manifest files[{index}].path")
        digest = entry["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise SnapshotError(f"manifest files[{index}].sha256 is invalid")
        if target in paths:
            raise SnapshotError(f"duplicate manifest target: {target}")
        target_path = snapshot / target
        if not target_path.is_file() or target_path.is_symlink():
            raise SnapshotError(f"snapshot payload is missing or not a regular file: {target}")
        actual = sha256(target_path)
        if actual != digest:
            raise SnapshotError(
                f"snapshot payload checksum differs: {target} (expected {digest}, got {actual})"
            )
        paths.add(target)
        normalized.append(
            {"source": source_path.as_posix(), "path": target.as_posix(), "sha256": digest}
        )

    allowed = paths | {Path(MANIFEST_NAME), Path(CHECKSUMS_NAME)}
    actual_files = {
        path.relative_to(snapshot)
        for path in snapshot.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    extras = sorted(path.as_posix() for path in actual_files - allowed)
    if extras:
        raise SnapshotError(f"snapshot contains untracked files: {', '.join(extras)}")
    expected_checksums = checksum_text(normalized)
    try:
        actual_checksums = (snapshot / CHECKSUMS_NAME).read_text(encoding="utf-8")
    except OSError as error:
        raise SnapshotError(f"cannot read {snapshot / CHECKSUMS_NAME}: {error}") from error
    if actual_checksums != expected_checksums:
        raise SnapshotError(f"{CHECKSUMS_NAME} differs from manifest")
    return {**manifest, "files": normalized}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "snapshot",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    args = parser.parse_args()
    try:
        manifest = verify(args.snapshot)
    except SnapshotError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f'verified {manifest["name"]} {manifest["version"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
