#!/usr/bin/env python3
"""Подставляет path-scoped правила проекта в контекст агента.

Claude загружает те же файлы нативно через `.claude/rules -> ../.harness/rules`.
Codex и Kimi используют этот adapter: на PreToolUse он смотрит, какие файлы будут
изменены, матчит путь против `paths:` каждого правила и отдаёт тело подходящего правила
через `additionalContext`. Одно правило на сессию отдаётся один раз, иначе каждая правка
жгла бы токены повторной вставкой.

Контракт одинаков для всех рантаймов: JSON со stdin, JSON в stdout, `exit 0`.
Гейт никогда не блокирует работу: он только добавляет контекст.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Project gates are generated source files, not a Python package. Importing the
# payload helper must not dirty every repository with `.harness/gates/__pycache__`.
sys.dont_write_bytecode = True
from runtime_payload import target_paths

MARKER_DIR = Path(tempfile.gettempdir()) / "harness-rules-injected"


class RuleConfigError(ValueError):
    """A rule would otherwise be loaded with broader scope than declared."""


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Переводит glob в регулярку. `**` пересекает разделители, `*` и `?` нет.

    Собственная реализация вместо fnmatch: fnmatch не различает `*` и `**`, из-за чего
    правило для `frontend/src/**` цепляло бы вообще всё.
    """
    out: list[str] = []
    i, n = 0, len(pattern)
    while i < n:
        ch = pattern[i]
        if ch == "*":
            if pattern.startswith("**", i):
                i += 2
                if pattern.startswith("/", i):
                    i += 1
                    out.append("(?:.*/)?")
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        elif ch in ".^$+{}[]|()\\":
            out.append("\\" + ch)
        else:
            out.append(ch)
        i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(glob: str, rel_path: str) -> bool:
    """Матчит glob против пути репозитория.

    Паттерн без слеша сверяется ещё и с именем файла: `*.tsx` означает «любой .tsx»,
    как в gitignore, а не «.tsx в корне». Паттерн со слешем матчится строго по пути.
    """
    rx = glob_to_regex(glob)
    if rx.match(rel_path):
        return True
    if "/" not in glob:
        return bool(rx.match(os.path.basename(rel_path)))
    return False


def parse_rule(path: Path) -> tuple[list[str], str]:
    """Возвращает (paths, тело). Правило без `paths:` считается всегда применимым."""
    text = path.read_text(encoding="utf-8")
    globs: list[str] = []
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            front, body = text[3:end], text[end + 4 :]
            if re.search(r"^globs:[^\S\n]*(?:$|\S)", front, re.MULTILINE):
                raise RuleConfigError(
                    f"{path}: unsupported frontmatter key 'globs'; use 'paths'"
                )
            # `[^\S\n]*` вместо `\s*`: иначе жадный `\s*` перепрыгивает перевод строки
            # и втягивает первый элемент многострочного YAML-списка вместе с дефисом.
            m = re.search(r"^paths:[^\S\n]*(\S.*)$", front, re.MULTILINE)
            if m:
                raw = m.group(1).strip()
                if raw.startswith("["):
                    globs = re.findall(r'["\']([^"\']+)["\']', raw)
                else:
                    globs = [raw.strip("\"'")]
            # Многострочный YAML-список: `paths:` и ниже строки с дефисом
            if not globs and re.search(r"^paths:[^\S\n]*$", front, re.MULTILINE):
                tail = front.split("paths:", 1)[1]
                for line in tail.splitlines():
                    m2 = re.match(r'\s*-\s*["\']?([^"\'\s]+)["\']?\s*$', line)
                    if m2:
                        globs.append(m2.group(1))
                    elif line.strip() and not line.startswith(" "):
                        break
            if re.search(r"^paths:", front, re.MULTILINE) and not globs:
                raise RuleConfigError(f"{path}: 'paths' must contain at least one glob")
    return globs, body.strip()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    repo = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    rules_dir = Path(repo) / ".harness" / "rules"
    if not rules_dir.is_dir():
        return 0

    paths = target_paths(payload)
    if not paths:
        return 0

    rel_paths = []
    for p in paths:
        try:
            rel_paths.append(str(Path(p).resolve().relative_to(Path(repo).resolve())))
        except (ValueError, OSError):
            rel_paths.append(p)

    session = str(payload.get("session_id") or "nosession")
    MARKER_DIR.mkdir(parents=True, exist_ok=True)

    chunks: list[str] = []
    for rule in sorted(rules_dir.glob("*.md")):
        try:
            globs, body = parse_rule(rule)
        except RuleConfigError as exc:
            print(f"RULES-CONFIG: {exc}", file=sys.stderr)
            return 2
        except Exception:
            continue
        if not body:
            continue
        if globs:
            if not any(
                matches(glob, rel) for rel in rel_paths for glob in globs
            ):
                continue

        key = hashlib.sha256(f"{session}:{repo}:{rule.name}".encode()).hexdigest()[:24]
        marker = MARKER_DIR / key
        if marker.exists():
            continue
        marker.write_text("", encoding="utf-8")
        chunks.append(f"### Правило проекта: {rule.stem}\n\n{body}")

    if not chunks:
        return 0

    context = (
        "Правила этого проекта, относящиеся к файлу, который ты сейчас правишь. "
        "Они перекрывают глобальные умолчания.\n\n" + "\n\n---\n\n".join(chunks)
    )
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        },
        sys.stdout,
        ensure_ascii=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
