# Sachkov Inside workspace

Приватный workspace всего проекта Sachkov Inside. Здесь хранятся общие продуктовые документы,
исследования и решения. Код отдельных частей продукта живёт в самостоятельных Git repositories.

## Репозитории

- `workspace` — этот repository: общая продуктовая картина и cross-repo решения;
- `inside-landing` — публичный landing;
- `platform` — будущая Membership-платформа;
- `telegram-bot` — Telegram-интеграция.

Актуальная карта находится в [`REPOSITORIES.md`](REPOSITORIES.md).

Каждый repository автономен: имеет собственную историю, настройки, CI и в будущем собственный
harness. Build, test и deploy дочернего repository не должны зависеть от наличия этого workspace
на диске.

## VS Code

Открыть весь проект как multi-root workspace:

```bash
code inside.code-workspace
```

VS Code покажет workspace-документы и каждый repository отдельным корнем. Git operations нужно
выполнять в выбранном repository, а не сразу над всей директорией.
