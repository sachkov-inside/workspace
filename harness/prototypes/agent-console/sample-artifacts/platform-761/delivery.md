---
type: delivery
task: platform#761
head: e62f31be
verdict: merged
---
## Итог
Тест запуска воркера больше не падает на загруженном CI: срок теста обоснован замером и не меньше бюджета процесса. Код воркеров не менялся.

## Что нужно от тебя
Ничего.

## Куда смотреть в изменениях
Один файл: `apps/backend/test/unit/worker-startup-failure.test.ts`.
