# Sachkov Inside workspace

Workspace всего проекта Sachkov Inside. Здесь хранятся общие продуктовые и юридические документы и
подтверждённые решения. Код отдельных частей продукта живёт в самостоятельных Git repositories.

## Документы и репозитории

Для текущей модели материалов и серий читать
[brief материалов и серий](product/content-series-authoring-brief.md), для понятий —
[CONTEXT.md](CONTEXT.md), для начала редакционной работы —
[handoff](product/series-planning-handoff.md).

Owning repositories и их роли перечислены один раз в [REPOSITORIES.md](REPOSITORIES.md).
Общая архитектура первой поставки Platform описана в
[shared specification](docs/specifications/platform-v1.md); текущий продуктовый scope — в brief выше.

Каждый repository автономен: имеет собственную историю, настройки, CI и собственные инструкции.
Build, test и deploy дочернего repository не должны зависеть от наличия этого workspace на диске.

Задач и процесса разработки здесь нет. Процесс разработки Inside принадлежит repository
[`platform`](https://github.com/sachkov-inside/platform): его `WORKFLOW.md` и skills;
`inside-telegram` получает их копию. Задачи заводятся в repository, который владеет результатом.

## VS Code

Открыть весь проект как multi-root workspace:

```bash
code inside.code-workspace
```

VS Code покажет workspace-документы и каждый repository отдельным корнем. Git operations нужно
выполнять в выбранном repository, а не сразу над всей директорией.
