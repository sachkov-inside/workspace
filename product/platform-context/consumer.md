# Product context Platform

Этот каталог — версионированный snapshot подтверждённого продуктового контекста из
`sachkov-inside/workspace`. Файлы внутри snapshot являются локальным interface для разработки
Platform: build, test, run, deploy и работа агентов не читают Workspace, соседний checkout или
machine-local path.

## Как читать

- `platform-mvp-brief.md` задаёт продуктовый результат, пользователей, content model и границу v1.
- `manifest.json` фиксирует версию контракта, исходный Workspace commit, source path и SHA-256
  каждого поставленного файла.
- `verify.py` проверяет manifest, provenance shape, состав файлов и SHA-256 всего payload.
- `checksums.sha256` содержит переносимый список тех же SHA-256 для ручной проверки.
- Техническая спецификация и application ADR в Platform уточняют реализацию, но не переопределяют
  продуктовый scope. При противоречии остановите работу и поднимите Workspace issue.

Research reports, обсуждения issues и неподтверждённые working decisions не входят в snapshot.
Новый подтверждённый cross-repository документ добавляется только явным изменением manifest в
Workspace и новой версией контракта.

## Проверка

Из корня Platform:

```bash
python3 docs/product-context/verify.py
```

Эта команда только обнаруживает локальное расхождение и ничего не исправляет. Для проверки новой
версии относительно checkout Workspace используйте его source-side команду:

```bash
python3 product/platform-context/manage.py check \
  --snapshot /path/to/platform/docs/product-context
```

`check` сначала доказывает, что manifest и payload соответствуют заявленному historical Workspace
commit, затем сравнивает snapshot с текущими источниками. Путь передаётся только оператором команды
и никогда не сохраняется в Platform.

## Обновление

Обновление всегда выполняется отдельным Platform PR:

1. В Workspace изменить канонические документы и повысить `version` в
   `product/platform-context/contract.json` по SemVer: patch для уточнения без изменения смысла,
   minor для совместимого добавления и major для удаления или несовместимого изменения смысла.
2. После merge Workspace отрендерить candidate из чистых contract inputs в новый пустой каталог.
   Exporter сам запишет полный SHA текущего `HEAD` и откажется смешивать его с незакоммиченными
   источниками:

   ```bash
   python3 product/platform-context/manage.py render \
     --output /tmp/platform-product-context
   ```

3. Сравнить candidate с `docs/product-context/` в Platform. Команда `check` должна сообщить drift;
   она не изменяет target.
4. Явно заменить snapshot candidate-файлами, проверить checksums и application impact, затем
   оформить отдельный Platform PR со ссылкой на Workspace change.

Не редактируйте snapshot вручную и не запускайте автоматический pull/update в CI. CI может
проверять checksums; наличие новой upstream-версии остаётся видимым сигналом для отдельной задачи,
а не скрытой мутацией Platform.
