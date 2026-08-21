# PostgreSQL backup и recovery для Platform

Статус: исследовательская заготовка для workspace issue #44. Здесь только PostgreSQL backup,
PITR, аварийное восстановление и граница с migration rollback. Среды, delivery, secrets и общая
observability должны быть сведены ведущим в итоговую схему отдельно.

## Рекомендация

Для единственного production VPS нужен один зашифрованный pgBackRest repository во внешнем
S3-compatible object storage. Локальная копия на том же VPS не считается backup от потери VPS.
PostgreSQL непрерывно отправляет WAL через `archive_command`; full/diff/incr backup'ы уменьшают
объём копирования и время replay, но сами по себе не задают RPO. PostgreSQL прямо описывает PITR
как сочетание filesystem-level backup с непрерывной последовательностью WAL и требует, чтобы эта
последовательность начиналась не позже начала выбранного backup'а
([PostgreSQL: Continuous Archiving](https://www.postgresql.org/docs/current/continuous-archiving.html)).

Цели принимаются только по результату drill:

- **RPO <= 1 час:** в восстановленном cluster самая свежая подтверждённая запись не старше 60
  минут относительно момента имитированной потери VPS.
- **RTO <= 4 часа:** от объявления потери VPS до готовности восстановленного PostgreSQL принимать
  production workload, включая проверку данных и application smoke check, проходит не более 4
  часов.

Настройка `archive_timeout` ограничивает возраст незавершённого WAL segment, но не гарантирует
RPO при недоступном S3, ошибочной конфигурации или переполнении `pg_wal`. Поэтому конфигурация,
проверки repository и recovery drill являются одной системой, а не независимыми опциями.

## Базовая конфигурация

Шаблон фиксирует форму, а не реальные пути, endpoint или credentials:

```ini
# postgresql.conf
archive_mode = on
archive_command = 'pgbackrest --stanza=platform archive-push %p'
archive_timeout = '5min'
```

`archive_command` вызывается только для завершённых WAL segments; при слабой нагрузке
`archive_timeout` принудительно переключает segment. PostgreSQL предупреждает, что слишком малое
значение раздувает archive storage; пять минут оставляет большой запас до RPO 1 час без попытки
сделать WAL archive механизмом синхронной репликации
([PostgreSQL: WAL archiving и `archive_timeout`](https://www.postgresql.org/docs/current/runtime-config-wal.html#RUNTIME-CONFIG-WAL-ARCHIVING)).

```ini
# pgbackrest.conf; placeholders must be supplied outside version control
[platform]
pg1-path=<PGDATA>

[global]
repo1-type=s3
repo1-path=/platform/postgresql
repo1-s3-bucket=<bucket>
repo1-s3-endpoint=<endpoint>
repo1-s3-region=<region>
repo1-s3-key=<access-key>
repo1-s3-key-secret=<secret-key>
repo1-cipher-type=aes-256-cbc
repo1-cipher-pass=<independently-recoverable-random-passphrase>
repo1-retention-full=4
repo1-bundle=y
repo1-block=y
spool-path=/var/spool/pgbackrest
start-fast=y

[global:archive-push]
archive-async=y
process-max=2
```

Также нужен локальный `spool-path`, принадлежащий пользователю PostgreSQL. pgBackRest поддерживает
S3-compatible repository и требует заранее создать bucket; endpoint, region и URI style следует
проверить на выбранном provider
([pgBackRest: S3-compatible object store](https://pgbackrest.org/user-guide.html#s3-support)).
TLS certificate verification включена по умолчанию и не должна отключаться в production
([pgBackRest: `repo-storage-verify-tls`](https://pgbackrest.org/configuration.html#section-repository/option-repo-storage-verify-tls)).

`archive-async=y` полезен для latency object storage: pgBackRest отправляет готовые segments
параллельно, но возвращает PostgreSQL success только после безопасной записи требуемого segment в
archive. Spool содержит status, а не единственную копию WAL
([pgBackRest: asynchronous archive-push](https://pgbackrest.org/user-guide.html#async-archiving/async-archive-push)).
Начать следует с небольшого `process-max` и увеличить его только по измерениям, чтобы backup не
вытеснил production I/O.

pgBackRest шифрует repository client-side с `aes-256-cbc`, в том числе если object storage имеет
собственное encryption at rest
([pgBackRest: repository encryption](https://pgbackrest.org/configuration.html#section-repository/option-repo-cipher-type)).
Потеря `repo1-cipher-pass` равна потере backup, поэтому recovery drill обязан получать passphrase
не с восстанавливаемого VPS. Access key должен быть ограничен одним bucket/prefix; детали хранения
и ротации credentials относятся к отдельной части issue #44.

## Backup и retention

Начальный schedule для небольшой Platform:

| Операция | Частота | Назначение |
|---|---:|---|
| `--type=full backup` | еженедельно, воскресенье | Независимая база цепочки |
| `--type=diff backup` | ежедневно, понедельник-суббота | Копия изменений от последнего full; короткий restore chain |
| `--type=incr backup` | каждые 6 часов между daily backup'ами | Копия изменений от предыдущего backup; меньше данных для restore |
| `archive-push` | непрерывно | Фактический механизм RPO и PITR между backup'ами |

pgBackRest определяет full как независимый backup, diff как изменения после full, а incr как
изменения после любого предыдущего backup; для restore incr нужны все его зависимости
([pgBackRest: backup concepts](https://pgbackrest.org/user-guide.html#concept/backup)). Официальный
пример планирует weekly full и daily diff через cron; у pgBackRest нет встроенного scheduler
([pgBackRest: schedule a backup](https://pgbackrest.org/user-guide.html#quickstart/schedule-backup)).
В production лучше отдельные systemd timers с единым lock, запретом параллельных backup jobs и
явной проверкой exit code.

Начальная retention policy: `repo1-retention-full=4`, не задавать отдельные
`repo1-retention-diff` и `repo1-retention-archive`. Тогда diff/incr живут вместе со своим full, а
WAL по умолчанию сохраняется для неистёкших backup'ов. Incremental backup не имеет собственной
retention и удаляется с зависимым full/diff
([pgBackRest: retention](https://pgbackrest.org/user-guide.html#retention)). Это даёт примерно
трёх-четырёхнедельное PITR window при weekly full без риска случайно укоротить его более агрессивной
WAL retention. После четырёх недель нужно пересчитать policy по фактическим размерам full/diff/incr,
суточному WAL, длительности restore и стоимости S3; pgBackRest также рекомендует оценивать capacity
по измеренным backup sizes и WAL/day
([pgBackRest: create repository](https://pgbackrest.org/user-guide.html#quickstart/create-repository)).

## Проверка backup'ов

Наличие объектов в bucket не доказывает recoverability. Минимальный режим:

1. После первоначального `stanza-create`, после изменения PostgreSQL/pgBackRest config и ежедневно
   выполнять `pgbackrest --stanza=platform check`. `check` проверяет repository, конфигурацию
   archiving, создаёт restore point и переключает WAL, чтобы подтвердить доставку segment
   ([pgBackRest: check configuration](https://pgbackrest.org/user-guide.html#quickstart/check-configuration)).
2. После каждой backup job сохранять успешный exit code и проверять `pgbackrest --stanza=platform
   --output=json info`: status, timestamp stop, backup dependencies и WAL min/max. pgBackRest
   гарантирует, что требуемый для согласованности backup WAL range находится в archive до успешного
   завершения backup
   ([pgBackRest: backup information](https://pgbackrest.org/user-guide.html#quickstart/backup-info)).
3. Еженедельно выполнять `pgbackrest --stanza=platform --output=text verify`, либо
   `--set=<latest-label>` для ограниченной проверки. `verify` определяет, валидны ли backup'ы и WAL
   archives repository
   ([pgBackRest: verify command](https://pgbackrest.org/command.html#command-verify)).
4. Ежемесячно выполнять настоящий restore на чистую временную машину. Только он одновременно
   проверяет S3 access, encryption key, package/bootstrap instructions, throughput, WAL chain и
   прикладные assertions.

Если cluster создан с PostgreSQL data page checksums, pgBackRest автоматически проверяет их во
время backup и записывает invalid pages в manifest, но warning сам по себе не прерывает backup.
Поэтому любой checksum warning должен делать операционную job неуспешной
([pgBackRest: `checksum-page`](https://pgbackrest.org/command.html#command-backup/category-command/option-checksum-page)).

## Восстановление пустого VPS

Runbook обязан быть исполним без файлов с потерянного host.

1. Зафиксировать `t0` — время объявления incident — и держать новый PostgreSQL недоступным
   приложению до завершения validation.
2. Создать VPS с достаточным диском и пропускной способностью. Установить тот же PostgreSQL major,
   совместимый актуальный minor, тот же pgBackRest release и расширения. Physical data directory
   между PostgreSQL major versions несовместим; major upgrade требует dump/reload или `pg_upgrade`
   ([PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/)).
3. Восстановить отдельно хранимые declarative config, S3 credentials и
   `repo1-cipher-pass`; создать пустой `PGDATA` с правильными owner/mode и тот же `pg1-path`.
4. До изменения repository выполнить read-only `pgbackrest --stanza=platform --repo=1 info` и
   выбрать последний известный валидный backup set. Не запускать `stanza-create`: stanza уже
   существует в off-host repository.
5. Остановить PostgreSQL и выполнить latest recovery:

   ```bash
   pgbackrest --stanza=platform --repo=1 --process-max=<measured> restore
   ```

   pgBackRest требует остановленный cluster и пустой data directory; обычный restore выбирает
   latest backup, а PostgreSQL затем проигрывает WAL до конца доступного archive
   ([pgBackRest: restore a backup](https://pgbackrest.org/user-guide.html#quickstart/perform-restore),
   [pgBackRest: PITR](https://pgbackrest.org/user-guide.html#pitr)). Для известной логической порчи
   использовать точку до события:

   ```bash
   pgbackrest --stanza=platform --repo=1 \
     --type=time --target='<PostgreSQL timestamp with UTC offset>' \
     --target-action=promote restore
   ```

   pgBackRest сам записывает `restore_command` и recovery target в `postgresql.auto.conf`; target
   должен быть позже конца выбранного backup. Для повторной попытки сначала снова очистить target
   `PGDATA` или использовать документированный `--delta` только после осознанной проверки.
6. Запустить PostgreSQL, дождаться окончания recovery, проверить server log и зафиксировать время
   последней применённой transaction. PostgreSQL рекомендует проверить содержимое cluster до
   возврата обычного доступа
   ([PostgreSQL: recovering from continuous archive](https://www.postgresql.org/docs/current/continuous-archiving.html#BACKUP-PITR-RECOVERY)).
7. Выполнить SQL assertions: ожидаемые databases/extensions/migration version, referential sanity,
   последняя recovery marker; затем application smoke check. Зафиксировать `t_ready` и только после
   этого разрешить production traffic.

PostgreSQL WAL не восстанавливает внешние `postgresql.conf`, `pg_hba.conf` и `pg_ident.conf`, если
они лежат вне покрытого backup'ом data directory. Их воспроизводимость должна проверяться тем же
full-VPS drill
([PostgreSQL: archive caveat for configuration](https://www.postgresql.org/docs/current/continuous-archiving.html#BACKUP-ARCHIVING-WAL)).

## Recovery drill и измерение целей

Ежемесячный database drill:

1. Не менее суток перед drill раз в пять минут записывать UTC marker с уникальным drill ID и
   временем commit в служебную таблицу. Не выполнять `pg_switch_wal()` после marker: это намеренно
   измеряет обычный путь и действие `archive_timeout`.
2. В случайный момент зафиксировать `t0`, прекратить marker writes и запретить drill host любой
   доступ к исходному VPS; восстановить только из S3 на чистый host по runbook выше.
3. Найти максимальный восстановленный marker timestamp `t_marker`; измерить
   `observed_rpo = t0 - t_marker`. Pass: `observed_rpo <= 60 min`.
4. После database assertions и application smoke зафиксировать `t_ready`; измерить
   `observed_rto = t_ready - t0`. Pass: `observed_rto <= 4 h`.
5. Сохранить backup label, WAL max, размеры, download/replay durations, обе метрики и отклонения
   runbook. Drill считается failed при ручном поиске отсутствующего секрета/шага, даже если итоговое
   время уложилось в SLO.

Раз в квартал нужен full-VPS drill с тем же bootstrap, storage credentials и network isolation,
поскольку database-only drill не доказывает четырёхчасовое восстановление пустого VPS. Для
оперативной оценки риска между drill'ами PostgreSQL предоставляет `pg_stat_archiver` с
`last_archived_time`, `last_failed_time` и counters, но timestamp последней архивации не заменяет
проверку фактически восстановленных данных
([PostgreSQL: `pg_stat_archiver`](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ARCHIVER-VIEW)).

## Граница release rollback и migration recovery

Перед изменяющей schema migration release job может создать именованную точку и принудительно
завершить segment:

```sql
SELECT pg_create_restore_point('before_release_<id>');
SELECT pg_switch_wal();
```

После этого release продолжает migration только когда pgBackRest `check` или эквивалентная
проверка подтверждает segment в off-host archive. PostgreSQL документирует `pg_switch_wal()` как
способ без задержки отправить только что завершённую transaction в archive
([PostgreSQL: WAL control functions](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-BACKUP)).

Эта точка — аварийная страховка, не штатный rollback:

- continuous archive восстанавливает весь cluster, а не отдельную database или migration; для PITR
  нужна непрерывная WAL chain
  ([PostgreSQL: scope and requirements of PITR](https://www.postgresql.org/docs/current/continuous-archiving.html#BACKUP-ARCHIVING-WAL));
- recovery на `before_release_<id>` удалит все commits всего cluster после этой точки, включая
  корректные пользовательские записи;
- rollback container image после уже применённой migration безопасен только при schema,
  совместимой со старым приложением; destructive contract должен происходить отдельным поздним
  release после периода совместимости;
- transaction вокруг migration откатывает вошедшие в неё statements, но не все production-safe
  DDL можно выполнять в одном transaction block: например, `CREATE INDEX CONCURRENTLY` явно этого
  не допускает
  ([PostgreSQL: concurrent index build](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)).

Следствие для единой схемы выпуска: не объявлять «restore pre-release backup» обычным rollback.
Штатный путь — backward-compatible migration, rollback приложения и затем forward repair/down
migration, заранее проверенная на копии production. PITR требует owner decision о допустимой потере
всех post-target writes и отдельного incident runbook.

## Критерии готовности production recovery

- S3 repository физически вне production VPS; bucket/prefix и restore credentials проверены с
  чистого host.
- `check`, backup schedule, retention и `verify` выполнялись без ошибок полный retention cycle.
- Encryption key доступен recovery operator без исходного VPS; TLS verification включена.
- Последние database и full-VPS drills имеют `observed_rpo <= 60 min` и
  `observed_rto <= 4 h`.
- Drill восстановил latest state и отдельный PITR target; SQL assertions и application smoke
  перечислены в runbook, а не импровизируются во время incident.
- Release process отличает image rollback, migration rollback и destructive whole-cluster PITR.

## Первичные источники

- [PostgreSQL: Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [PostgreSQL: WAL archiving configuration](https://www.postgresql.org/docs/current/runtime-config-wal.html#RUNTIME-CONFIG-WAL-ARCHIVING)
- [PostgreSQL: WAL control functions](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-BACKUP)
- [PostgreSQL: `pg_stat_archiver`](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ARCHIVER-VIEW)
- [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/)
- [PostgreSQL: `CREATE INDEX`](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)
- [pgBackRest User Guide](https://pgbackrest.org/user-guide.html)
- [pgBackRest Configuration Reference](https://pgbackrest.org/configuration.html)
- [pgBackRest Command Reference](https://pgbackrest.org/command.html)
