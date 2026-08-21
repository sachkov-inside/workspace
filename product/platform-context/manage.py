#!/usr/bin/env python3
"""Render and compare the versioned Platform product-context snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from verify_snapshot import SnapshotError, checksum_text, read_json, relative_path, sha256, verify


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("product/platform-context/contract.json")
MANIFEST_NAME = "manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
ContractError = SnapshotError


def load_contract(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    contract = read_json(repo_root / CONTRACT_PATH)
    required = {"schemaVersion", "name", "version", "sourceRepository", "files"}
    if set(contract) != required:
        raise ContractError(
            f"contract keys must be exactly {sorted(required)}; got {sorted(contract)}"
        )
    if contract["schemaVersion"] != 1:
        raise ContractError("only contract schemaVersion 1 is supported")
    if not isinstance(contract["name"], str) or not contract["name"]:
        raise ContractError("contract name must be a non-empty string")
    if not isinstance(contract["sourceRepository"], str) or not contract["sourceRepository"]:
        raise ContractError("sourceRepository must be a non-empty string")
    if not isinstance(contract["version"], str) or not SEMVER.fullmatch(contract["version"]):
        raise ContractError("contract version must be SemVer MAJOR.MINOR.PATCH")
    if not isinstance(contract["files"], list) or not contract["files"]:
        raise ContractError("contract files must be a non-empty array")

    sources: set[Path] = set()
    targets: set[Path] = set()
    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(contract["files"]):
        if not isinstance(entry, dict) or set(entry) != {"source", "target"}:
            raise ContractError(f"files[{index}] must contain only source and target")
        source = relative_path(entry["source"], f"files[{index}].source")
        target = relative_path(entry["target"], f"files[{index}].target")
        if source in sources or target in targets:
            raise ContractError(f"duplicate source or target in files[{index}]")
        source_path = repo_root / source
        if not source_path.is_file() or source_path.is_symlink():
            raise ContractError(f"source must be a regular file: {source}")
        sources.add(source)
        targets.add(target)
        normalized.append({"source": source.as_posix(), "target": target.as_posix()})
    return {**contract, "files": normalized}


def expected_payload(contract: dict[str, Any], repo_root: Path) -> list[dict[str, str]]:
    return [
        {
            "source": entry["source"],
            "path": entry["target"],
            "sha256": sha256(repo_root / entry["source"]),
        }
        for entry in contract["files"]
    ]


def source_revision(contract: dict[str, Any], repo_root: Path) -> str:
    inputs = [CONTRACT_PATH.as_posix(), *(entry["source"] for entry in contract["files"])]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        for path in inputs:
            committed = subprocess.run(
                ["git", "show", f"HEAD:{path}"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            ).stdout
            if committed != (repo_root / path).read_bytes():
                raise ContractError(f"contract input differs from HEAD: {path}")
    except (OSError, subprocess.CalledProcessError) as error:
        raise ContractError("contract inputs must exist in the current Git HEAD") from error
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ContractError("current Git HEAD is not a full lowercase SHA")
    return revision


def git_blob(repo_root: Path, revision: str, path: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "show", f"{revision}:{path}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise ContractError(f"cannot resolve provenance {revision}:{path}") from error


def verify_provenance(manifest: dict[str, Any], repo_root: Path) -> None:
    revision = manifest["source"]["revision"]
    try:
        historical = json.loads(git_blob(repo_root, revision, CONTRACT_PATH.as_posix()))
    except json.JSONDecodeError as error:
        raise ContractError(f"historical contract is invalid at {revision}") from error
    expected_identity = (
        historical.get("schemaVersion"),
        historical.get("name"),
        historical.get("version"),
        historical.get("sourceRepository"),
    )
    actual_identity = (
        manifest["schemaVersion"],
        manifest["name"],
        manifest["version"],
        manifest["source"]["repository"],
    )
    historical_files = historical.get("files")
    if not isinstance(historical_files, list):
        raise ContractError(f"historical contract has no file list at {revision}")
    expected_files = [
        {"source": entry.get("source"), "path": entry.get("target")}
        for entry in historical_files
        if isinstance(entry, dict)
    ]
    actual_files = [
        {"source": entry["source"], "path": entry["path"]} for entry in manifest["files"]
    ]
    if expected_identity != actual_identity or expected_files != actual_files:
        raise ContractError(f"manifest differs from its historical contract at {revision}")
    for entry in manifest["files"]:
        blob = git_blob(repo_root, revision, entry["source"])
        if hashlib.sha256(blob).hexdigest() != entry["sha256"]:
            raise ContractError(
                f'manifest payload differs from provenance {revision}:{entry["source"]}'
            )


def render(output: Path, repo_root: Path = REPO_ROOT) -> None:
    contract = load_contract(repo_root)
    revision = source_revision(contract, repo_root)
    files = expected_payload(contract, repo_root)
    manifest = {
        "schemaVersion": contract["schemaVersion"],
        "name": contract["name"],
        "version": contract["version"],
        "source": {"repository": contract["sourceRepository"], "revision": revision},
        "files": files,
    }
    if output.exists():
        if not output.is_dir() or output.is_symlink():
            raise ContractError(f"output exists and is not a regular directory: {output}")
        if any(output.iterdir()):
            raise ContractError(f"output directory must be empty: {output}")
    else:
        output.mkdir(parents=True)

    for entry in contract["files"]:
        destination = output / entry["target"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / entry["source"], destination)
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / CHECKSUMS_NAME).write_text(checksum_text(files), encoding="utf-8")


def check(snapshot: Path, repo_root: Path = REPO_ROOT) -> None:
    manifest = verify(snapshot)
    verify_provenance(manifest, repo_root)
    contract = load_contract(repo_root)
    expected = expected_payload(contract, repo_root)
    identity_matches = (
        manifest["schemaVersion"] == contract["schemaVersion"]
        and manifest["name"] == contract["name"]
        and manifest["source"]["repository"] == contract["sourceRepository"]
    )
    if not identity_matches:
        raise ContractError("snapshot identity differs from the Workspace contract")
    if manifest["files"] == expected and manifest["version"] == contract["version"]:
        return
    if manifest["files"] != expected and manifest["version"] == contract["version"]:
        raise ContractError(
            "Workspace payload changed without a contract version bump; bump contract.json first"
        )
    raise ContractError(
        f'Platform snapshot {manifest["version"]} differs from Workspace contract '
        f'{contract["version"]}; render and review an explicit Platform update'
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    render_parser = commands.add_parser("render", help="render into a new or empty directory")
    render_parser.add_argument("--output", required=True, type=Path)
    for name in ("verify", "check"):
        command = commands.add_parser(name)
        command.add_argument("--snapshot", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "render":
            render(args.output)
            print(f"rendered {args.output}")
        elif args.command == "verify":
            manifest = verify(args.snapshot)
            print(f'verified {manifest["name"]} {manifest["version"]}')
        else:
            check(args.snapshot)
            print("Platform snapshot matches current Workspace product context")
    except ContractError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
