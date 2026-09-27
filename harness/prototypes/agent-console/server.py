#!/usr/bin/env python3
"""PROTOTYPE — agent console. Throwaway code on branch prototype/agent-console.

Question: which view and which artifact structure let the owner control agent work
from above without reading code? Three UI variants on one page, switch with ?variant=A|B|C.

Run:  python3 harness/prototypes/agent-console/server.py   → http://127.0.0.1:4480
Read-only: live agents come from `herdr agent list`, PR state from `gh`, artifacts from
./sample-artifacts. Nothing is written except review files produced by Plannotator.
"""

from __future__ import annotations

import json
import mimetypes
import re
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "sample-artifacts"
WORKSPACE = Path("/Users/dev/Work/Products/inside")
ALLOWED_FILE_ROOTS = [ARTIFACTS, WORKSPACE / "repositories"]
PORT = 4480
_cache: dict[str, tuple[float, object]] = {}


def cached(key: str, ttl: float, produce):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = produce()
    _cache[key] = (now, value)
    return value


def run_json(args: list[str], timeout: int = 15):
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)
        return json.loads(out.stdout)
    except Exception as error:  # prototype: surface the failure, keep serving
        return {"error": f"{args[0]}: {error}"}


def live_agents() -> list[dict]:
    raw = run_json(["herdr", "agent", "list"])
    agents = raw.get("result", {}).get("agents", []) if isinstance(raw, dict) else []
    result = []
    for agent in agents:
        tokens = agent.get("tokens") or {}
        branch = (tokens.get("branch") or "").split(" ")[0].rstrip("*")
        issue = re.match(r"^[a-z]+/(\d+)-", branch)
        cwd = agent.get("cwd", "")
        result.append({
            "runtime": agent.get("agent"),
            "status": agent.get("agent_status"),
            "title": agent.get("terminal_title_stripped", ""),
            "repo": tokens.get("repo") or Path(cwd).name,
            "branch": branch or None,
            "issue": int(issue.group(1)) if issue else None,
            "session": (agent.get("agent_session") or {}).get("value"),
            "cwd": cwd,
            "pane": agent.get("pane_id"),
        })
    return result


def pr_state(repo: str, number: int) -> dict:
    data = run_json([
        "gh", "pr", "view", str(number), "-R", f"sachkov-inside/{repo}",
        "--json", "number,title,state,mergedAt,url,statusCheckRollup,additions,deletions,changedFiles",
    ])
    if "error" in data:
        return {"number": number, "error": data["error"]}
    checks = data.pop("statusCheckRollup", []) or []
    conclusions = [c.get("conclusion") or c.get("state") or "PENDING" for c in checks]
    data["checks"] = {
        "total": len(conclusions),
        "passed": sum(c in ("SUCCESS", "NEUTRAL", "SKIPPED") for c in conclusions),
        "failed": sum(c in ("FAILURE", "TIMED_OUT", "CANCELLED", "ERROR") for c in conclusions),
    }
    return data


def read_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def load_tasks() -> list[dict]:
    tasks = []
    for folder in sorted(p for p in ARTIFACTS.iterdir() if p.is_dir()):
        meta = json.loads((folder / "task.json").read_text(encoding="utf-8"))
        artifacts = {}
        for kind in ("decisions", "spec", "breakdown", "plan", "delivery", "handoff", "review"):
            md = read_text(folder / f"{kind}.md")
            facts = folder / f"{kind}.json"
            if md is None and not facts.exists():
                continue
            artifacts[kind] = {
                "markdown": md,
                "facts": json.loads(facts.read_text(encoding="utf-8")) if facts.exists() else None,
                "path": str(folder / f"{kind}.md"),
                "modified": int((folder / f"{kind}.md").stat().st_mtime) if md is not None else None,
            }
        meta["folder"] = folder.name
        meta["artifacts"] = artifacts
        meta["prs"] = [
            cached(f"pr:{meta['repo']}:{n}", 300, lambda n=n: pr_state(meta["repo"], n))
            for n in meta.get("prs", [])
        ]
        tasks.append(meta)
    return tasks


def state() -> dict:
    return {
        "generatedAt": int(time.time()),
        "agents": cached("agents", 5, live_agents),
        "tasks": load_tasks(),
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path == "/":
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif url.path == "/api/state":
            self._send(200, json.dumps(state(), ensure_ascii=False).encode(), "application/json")
        elif url.path == "/file":
            target = Path(parse_qs(url.query).get("p", [""])[0]).resolve()
            if not any(target.is_relative_to(root) for root in ALLOWED_FILE_ROOTS) or not target.is_file():
                self._send(404, b"not found", "text/plain")
                return
            kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self._send(200, target.read_bytes(), kind)
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *_args) -> None:
        pass


if __name__ == "__main__":
    print(f"PROTOTYPE agent console → http://127.0.0.1:{PORT}/?variant=A")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
