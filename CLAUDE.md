# CLAUDE.md

@AGENTS.md

Канон репозитория живёт в `AGENTS.md` и общий для всех агентов. Этот файл только мост:
содержательные правки идут туда.

Claude-специфика:

- Правила по путям Claude Code загружает нативно из `.claude/rules`, это symlink на
  канонический каталог `.harness/rules`. `paths:` обрабатывает сам runtime.
- Скиллы проекта лежат в `.harness/skills/`, `.claude/skills` это симлинк на них.
- Хуки сессии описаны в `.claude/settings.json`, таймауты в **секундах**. Они подключают
  safety guard; quality verification запускается агентом явно по Test Plan задачи.
