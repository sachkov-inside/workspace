# Sachkov Inside workspace

Приватный workspace всего проекта Sachkov Inside. Здесь хранятся общие продуктовые документы и
подтверждённые решения. Код отдельных частей продукта живёт в самостоятельных Git repositories.

## Репозитории

- `workspace` — этот repository: общая продуктовая картина и cross-repo решения;
- `inside-landing` — публичный landing;
- `platform` — Membership-платформа.

Актуальная карта находится в [`REPOSITORIES.md`](REPOSITORIES.md).
Cross-repository архитектура и этапы первой версии Platform описаны в
[`docs/specifications/platform-v1.md`](docs/specifications/platform-v1.md).

Каждый repository автономен: имеет собственную историю, настройки, CI и в будущем собственный
harness. Build, test и deploy дочернего repository не должны зависеть от наличия этого workspace
на диске.

Общий product harness хранится в [`harness/`](harness/) и устанавливается в каждый repository
управляемой project-local копией. Архитектура и release lifecycle описаны в
[`HARNESS.md`](HARNESS.md), а общий путь от issue до owner-controlled merge — в
[`WORKFLOW.md`](WORKFLOW.md).

## VS Code

Открыть весь проект как multi-root workspace:

```bash
code inside.code-workspace
```

VS Code покажет workspace-документы и каждый repository отдельным корнем. Git operations нужно
выполнять в выбранном repository, а не сразу над всей директорией.
