# Переход Inside на руководства: план поставки и аудит задач

Снимок планирования: 08.09.2026. На старте проверены все 45 открытых Platform issues;
появившаяся во время работы #445 добавлена отдельно. Новые задачи этой поставки перечислены
ниже и не входят в исходные 46. Актуальный статус исполнения всегда проверяется в GitHub.

Общая продуктовая модель имеет одну authority:
[руководства и материалы](content-series-authoring-brief.md).
Этот документ фиксирует последовательность и disposition backlog, не дублирует спецификации.
Общий delivery parent — [Workspace #156](https://github.com/sachkov-inside/workspace/issues/156),
связанный с существующим Human Backlog outcome #110. Issue #157 и документный PR фиксируют
результат планирования; приложение, данные покупателей и production в этой сессии не менялись.

## Последовательность

1. Зафиксировать общее решение и локальный контракт Platform. Инвентаризировать все места,
   где Series является identity, API, маршрутом, авторским пакетом или контекстом чтения.
2. Мигрировать все серии 1:1 и авторскую базу с сохранением существующих данных и интерфейса.
   Нынешние два главных комплекта содержат 25 и 17 материалов; третий — 5. Это снимок локальной
   редакционной базы, не опубликованный каталог. Перед миграцией снять новый inventory.
3. Добавить главы и материалы вне маршрута. Артефакты получают отдельный жизненный цикл и
   раздел, с тем же авторитетным доступом к ресурсам. Полный импорт расширяет прежний пилот.
4. Параллельно выбрать коммерческие условия и обновить платёжный контракт. Существующие
   foundation #404/#405 не переоткрываются; #453/#454 расширяют их. Открытые #407–#415
   поставляют прежние и новые сценарии в одной системе оплаты.
5. После продуктовых решений собрать самостоятельные страницы, воронки двух руководств и
   отчёт с честным различением переходов, прав и подтверждённых покупок.
6. Принять полный путь на двух руководствах. #413 владеет DEMO оплаты, #458 — общей
   интеграцией руководств. #414 сохраняет отдельное разрешение на реальные продажи;
   публикация конкретных материалов и внешние сообщения также разрешаются отдельно.

Объединение руководств и наборы покупок отложены. Закладывать универсальный marketplace,
новые аудитории, чаты каждого продукта или новый платёжный сервис эта поставка не требует.

## Созданные задачи

Native parent/sub-issues задают иерархию. Native blocked-by задаёт обязательный порядок;
в таблице видны непосредственные зависимости. Общие parent не заменяют отдельный результат
ребёнка. Существующий billing parent остаётся Workspace #148 → Platform #401.

| Задача | Результат | Зависимости |
| --- | --- | --- |
| [workspace #156](https://github.com/sachkov-inside/workspace/issues/156) | Перевести Inside на руководства: содержание, отдельные продажи и подписка | [platform #414](https://github.com/sachkov-inside/platform/issues/414) |
| [workspace #157](https://github.com/sachkov-inside/workspace/issues/157) | Зафиксировать переход на руководства и согласовать весь открытый backlog Platform | Нет предварительных blockers |
| [workspace #158](https://github.com/sachkov-inside/workspace/issues/158) | Определить условия покупки руководств, подписки и участия в сообществе | Нет предварительных blockers |
| [workspace #159](https://github.com/sachkov-inside/workspace/issues/159) | Упаковать первые руководства и определить путь от рекламы к покупке | Нет предварительных blockers |
| [platform #446](https://github.com/sachkov-inside/platform/issues/446) | Specification: руководства с главами, артефактами и самостоятельной покупкой | Нет предварительных blockers |
| [platform #447](https://github.com/sachkov-inside/platform/issues/447) | Описать модель руководства и безопасный переход с Series | [workspace #157](https://github.com/sachkov-inside/workspace/issues/157) |
| [platform #448](https://github.com/sachkov-inside/platform/issues/448) | Перевести существующие серии в руководства с сохранением интерфейса и данных | [platform #447](https://github.com/sachkov-inside/platform/issues/447) |
| [platform #449](https://github.com/sachkov-inside/platform/issues/449) | Дать автору главы руководства и материалы вне основного маршрута | [platform #448](https://github.com/sachkov-inside/platform/issues/448) |
| [platform #450](https://github.com/sachkov-inside/platform/issues/450) | Создавать и использовать отдельный раздел артефактов руководства | [platform #449](https://github.com/sachkov-inside/platform/issues/449), [platform #453](https://github.com/sachkov-inside/platform/issues/453) |
| [inside-content #8](https://github.com/sachkov-inside/inside-content/issues/8) | Перевести авторскую базу и инструменты с серий на руководства | [platform #447](https://github.com/sachkov-inside/platform/issues/447) |
| [platform #451](https://github.com/sachkov-inside/platform/issues/451) | Довести перенос руководства из Inside Content до полного авторского процесса | [platform #449](https://github.com/sachkov-inside/platform/issues/449), [platform #450](https://github.com/sachkov-inside/platform/issues/450), [inside-content #8](https://github.com/sachkov-inside/inside-content/issues/8), [platform #289](https://github.com/sachkov-inside/platform/issues/289) |
| [platform #452](https://github.com/sachkov-inside/platform/issues/452) | Расширить контракт оплаты на разовую покупку руководства | [workspace #158](https://github.com/sachkov-inside/workspace/issues/158), [platform #447](https://github.com/sachkov-inside/platform/issues/447) |
| [platform #453](https://github.com/sachkov-inside/platform/issues/453) | Выдавать доступ к купленному руководству независимо от подписки | [platform #452](https://github.com/sachkov-inside/platform/issues/452), [platform #448](https://github.com/sachkov-inside/platform/issues/448) |
| [platform #454](https://github.com/sachkov-inside/platform/issues/454) | Настраивать цены и предложения отдельных руководств наряду с подпиской | [platform #452](https://github.com/sachkov-inside/platform/issues/452), [platform #448](https://github.com/sachkov-inside/platform/issues/448) |
| [platform #455](https://github.com/sachkov-inside/platform/issues/455) | Показать самостоятельную страницу и покупку каждого руководства | [platform #449](https://github.com/sachkov-inside/platform/issues/449), [platform #450](https://github.com/sachkov-inside/platform/issues/450), [platform #411](https://github.com/sachkov-inside/platform/issues/411), [workspace #159](https://github.com/sachkov-inside/workspace/issues/159), [workspace #158](https://github.com/sachkov-inside/workspace/issues/158) |
| [platform #456](https://github.com/sachkov-inside/platform/issues/456) | Связать воронки и аналитику с конкретными руководствами | [platform #455](https://github.com/sachkov-inside/platform/issues/455), [workspace #159](https://github.com/sachkov-inside/workspace/issues/159), [platform #333](https://github.com/sachkov-inside/platform/issues/333), [platform #337](https://github.com/sachkov-inside/platform/issues/337), [inside-telegram #58](https://github.com/sachkov-inside/inside-telegram/issues/58) |
| [inside-telegram #58](https://github.com/sachkov-inside/inside-telegram/issues/58) | Поддержать воронки отдельных руководств по общему продуктовому контракту | [workspace #159](https://github.com/sachkov-inside/workspace/issues/159), [platform #452](https://github.com/sachkov-inside/platform/issues/452) |
| [platform #458](https://github.com/sachkov-inside/platform/issues/458) | Принять полный путь руководства от миграции до покупки и использования | [platform #451](https://github.com/sachkov-inside/platform/issues/451), [platform #455](https://github.com/sachkov-inside/platform/issues/455), [platform #456](https://github.com/sachkov-inside/platform/issues/456), [platform #413](https://github.com/sachkov-inside/platform/issues/413) |

## Открытые решения

Workspace #158 собирает срок разового доступа, включённые обновления/редакции, каталог подписки,
цены, состав общих/дополнительных материалов, судьбу изменённого купленного состава, прежние
бессрочные права, чат и поддержку. Ранее предложенные в беседе варианты не получили ответа.
Зависимые commercial tasks не объявлены ready по умолчанию; #452 должен уточнить их контракт
и readiness после принятия новой модели. Workspace #159 готовит две конкретные упаковки,
а не запускает рекламу или рассылки.

Platform #447 уточняет поведение глав и supplementary состава, включая расчёт прогресса,
допустимые размещения, опубликованный состав и версии. Новые UI требуют принятия по обычному
frontend-delivery; это не блокирует отдельное сохранение нынешнего UI при переименовании.

## Аудит всех исходных задач Platform

У затронутых issues обновлены названия, где это нужно, и добавлен верхний раздел с точной новой
границей. Прежнее тело сохранено как контекст исполнения; верхнее уточнение имеет приоритет
только в названной области. Закрытые issues, активные claims, чужие ветки и PR не переписаны.

| Issue | Действие | Причина / граница |
| --- | --- | --- |
| [#178](https://github.com/sachkov-inside/platform/issues/178) Specification: Доставить Media, файлы и видео Platform v1 | Сохранена без изменения | Media aggregate сохраняет свой последний provider gate; новый artifact lifecycle вынесен в #450, MaterialAsset ownership не меняется этим аудитом. |
| [#184](https://github.com/sachkov-inside/platform/issues/184) Провести Kinescope production acceptance перед релизом Platform | Сохранена без изменения | Существующая credentialed Kinescope production-приёмка сохраняется; guide-only access проверяется в новых #453/#458, без раздувания старого gate. |
| [#245](https://github.com/sachkov-inside/platform/issues/245) Добавить production observability и synthetic journeys Platform | Уточнены требования | В будущую матрицу synthetic journeys включить открытие руководства, сохранение контекста, выдачу разрешённого артефакта и покупку конкретного руководства после реализации соответствующих этапов. |
| [#273](https://github.com/sachkov-inside/platform/issues/273) Prototype: выбрать интерфейс Kafka-трека и пошаговой лаборатории | Сохранена без изменения | Отложенная Мастерская; Workshop Track не является бывшей Series. |
| [#274](https://github.com/sachkov-inside/platform/issues/274) Specification: доставить первый Kafka Track Мастерской | Сохранена без изменения | Отложенная самостоятельная Workshop модель; не конвертируется в руководство. |
| [#278](https://github.com/sachkov-inside/platform/issues/278) Исследовать проверку design и implementation Kafka Case | Сохранена без изменения | Исследование оценки Kafka Case остаётся отложенным; не связано с миграцией Series. |
| [#279](https://github.com/sachkov-inside/platform/issues/279) Публиковать Workshop content и сохранять прогресс лабораторий | Сохранена без изменения | Версионированный Workshop publication/progress остаётся отдельным и отложенным. |
| [#281](https://github.com/sachkov-inside/platform/issues/281) Реализовать полноценный frontend Мастерской и Kafka Track | Сохранена без изменения | Отложенный UI Мастерской не включается в первую миграцию. |
| [#282](https://github.com/sachkov-inside/platform/issues/282) Подготовить C# и Python variants и выбранную проверку Kafka Case | Сохранена без изменения | C#/Python Case variants и evaluator не являются артефактами руководства автоматически. |
| [#283](https://github.com/sachkov-inside/platform/issues/283) Провести end-to-end приёмку первого Kafka Track | Сохранена без изменения | Приёмка Kafka Track сохраняет исходный отложенный scope. |
| [#289](https://github.com/sachkov-inside/platform/issues/289) Prototype: проверить перенос материала и руководства из Inside Content | Уточнены требования; обновлено название | Пилот переносит самостоятельный Material и руководство; формат Material «гайд» не переименовывается в руководство. |
| [#304](https://github.com/sachkov-inside/platform/issues/304) Specification: связать Telegram-воронки с платформой и пройти сквозную приёмку | Уточнены требования | Цели контентных ссылок — руководства и самостоятельные материалы; старые Series links должны сохраняться через #448. |
| [#323](https://github.com/sachkov-inside/platform/issues/323) Specification: отмечать материалы изученными и видеть прогресс руководств | Уточнены требования; обновлено название | При переходе #448 термин Series становится руководством; общий Material, ручной read/unread и published composition сохраняются. |
| [#324](https://github.com/sachkov-inside/platform/issues/324) Specification: продолжать незавершённое изучение с главной | Уточнены требования | Continue работает для любого Account, включая покупателя отдельного руководства без подписки. |
| [#325](https://github.com/sachkov-inside/platform/issues/325) Specification: показывать посещаемость руководств и их материалов | Уточнены требования; обновлено название | Предмет отчёта включает руководства и их материалы. |
| [#330](https://github.com/sachkov-inside/platform/issues/330) Сохранять открытия и возвращать незавершённые материалы для главной | Уточнены требования | После миграции сохранять контекст руководства и прямое открытие Material; доступ проверять общим ContentAccess, чтобы собственная покупка переживала отмену подписки. |
| [#331](https://github.com/sachkov-inside/platform/issues/331) Согласовать персональную главную с блоком «Продолжить изучение» | Уточнены требования | В proof использовать термин «Руководство» и дополнить сценарии состоянием guide-only buyer и expired subscription + independently purchased guide после #453. |
| [#333](https://github.com/sachkov-inside/platform/issues/333) Определить метрики руководств, материалов и переходов к покупке | Уточнены требования; обновлено название | Дополнить decision contract сущностью руководства: separate page view и material body view, контекст входа, общий Material в двух руководствах, supplementary/artifact interactions и переход к checkout. |
| [#334](https://github.com/sachkov-inside/platform/issues/334) Собирать события руководств и материалов по принятому контракту | Уточнены требования; обновлено название | После принятия #333 сохранять stable guide identity и контекст события, если они выбраны в контракте; migration aliases не создают второй объект аналитики. |
| [#335](https://github.com/sachkov-inside/platform/issues/335) Согласовать отчёт автора по руководствам и материалам | Уточнены требования; обновлено название | После #333 показать выбранные показатели руководств и drill-down к материалам/действиям; не суммировать shared Material/unique visits как независимых людей. |
| [#336](https://github.com/sachkov-inside/platform/issues/336) Показать автору отчёт по руководствам и материалам на реальных данных | Уточнены требования; обновлено название | Подключить только принятые guide-level показатели #333/#335. |
| [#337](https://github.com/sachkov-inside/platform/issues/337) Определить учёт покупок руководств и подписок для аналитики | Уточнены требования; обновлено название | Исследовать оба authoritative lifecycle: разовая покупка конкретного руководства и подписка/renewal. |
| [#355](https://github.com/sachkov-inside/platform/issues/355) Подготовить инфраструктуру и пройти полную приёмку нового production-релиза | Уточнены требования | Существующая owner-led production приёмка сохраняет границы и ранее выданные разрешения своей сессии. |
| [#367](https://github.com/sachkov-inside/platform/issues/367) Подтвердить живую приёмку Telegram перед production | Уточнены требования | Контролируемый free Material/Series сценарий сохраняется; после #448 используется руководство с проверкой старой ссылки. |
| [#380](https://github.com/sachkov-inside/platform/issues/380) Prototype: сравнить гостевую главную с руководствами Inside | Уточнены требования; обновлено название | Подготовить следующий proof с руководствами как самостоятельными продуктами: результат, состав, публичный фрагмент и переход к отдельной покупке либо подписке по решениям #158/#159. |
| [#390](https://github.com/sachkov-inside/platform/issues/390) Восстановить загрузку видео в production Editor и объяснять отказ | Сохранена без изменения | Текущий production upload defect относится к Material/Video, не требует изменения контракта из-за нового имени. |
| [#401](https://github.com/sachkov-inside/platform/issues/401) Specification: покупка руководств, подписка и управление доступом Inside | Уточнены требования; обновлено название | Итог расширен: покупка отдельного руководства плюс действующая подписка, независимые scoped права, admin/кабинет/уведомления и DEMO обоих путей. |
| [#402](https://github.com/sachkov-inside/platform/issues/402) Подтвердить терминалы Т-Банка и параметры кассы для Inside | Уточнены требования | Capability matrix должна отдельно покрывать обычную разовую покупку руководства, subscription initial/recurring и возвраты/чеки. |
| [#407](https://github.com/sachkov-inside/platform/issues/407) Принимать оплату руководства или подписки и восстанавливать результат Т-Банка | Уточнены требования; обновлено название | Поставить два purchase paths по #452: one-time Guide purchase → самостоятельный grant и subscription → paid period. |
| [#408](https://github.com/sachkov-inside/platform/issues/408) Продлевать подписку, отменять списания и менять тариф или способ оплаты | Уточнены требования | Recurring/upgrade/downgrade/cancel действуют только на Subscription. |
| [#409](https://github.com/sachkov-inside/platform/issues/409) Управлять покупками руководств, подписками и возвратами через API и MCP | Уточнены требования; обновлено название | Управление охватывает разовые покупки руководств и подписки: target/mode видны в history/audit; owner видит quote/order/payment/fulfilment отдельно. |
| [#410](https://github.com/sachkov-inside/platform/issues/410) Уведомлять о покупке руководств и событиях подписки | Уточнены требования; обновлено название | Добавить служебные события покупки/выдачи/возврата конкретного руководства по #452. |
| [#411](https://github.com/sachkov-inside/platform/issues/411) Показать покупку руководств, подписку и платёжный кабинет | Уточнены требования; обновлено название | Checkout различает разовую покупку выбранного руководства и подписку; показывает утверждённые состав, цену, срок/обновления, уже имеющийся доступ и правильные согласия. |
| [#412](https://github.com/sachkov-inside/platform/issues/412) Разместить юридические документы и реквизиты на сайте, в футере и формах | Уточнены требования | Юридический комплект и версии согласий должны покрывать отдельно покупку руководства и подписку по Workspace #158/#149. |
| [#413](https://github.com/sachkov-inside/platform/issues/413) Пройти DEMO покупки руководств, подписки, чеков и доступа | Уточнены требования; обновлено название | Добавить DEMO one-off Guide A, denied B, shared resource, A + subscription → expiry/cancel, refund одного источника при другом действующем праве, неизвестный/поздний/повторный callback, confirmed payment с отложенной выдачей. |
| [#414](https://github.com/sachkov-inside/platform/issues/414) Подготовить и подтвердить запуск продаж руководств и подписки | Уточнены требования; обновлено название | Открытие продаж включает разовые руководства и подписку только после принятия соответствующих scope/цен/обновлений/чата #158 и DEMO #413. |
| [#415](https://github.com/sachkov-inside/platform/issues/415) Передавать права участия в сообществе из Platform в Telegram | Уточнены требования | Community capability остаётся независимой от чтения руководства. |
| [#421](https://github.com/sachkov-inside/platform/issues/421) Подготовить Platform к переносу на sachkov.dev | Уточнены требования | При совмещении с #448 проверить композицию domain redirect и legacy /series → canonical guide mapping с сохранением разрешённых query/hash и без циклов. |
| [#423](https://github.com/sachkov-inside/platform/issues/423) Исправить ширину заметок и отступ плашки на главной | Сохранена без изменения | Чистое исправление ширины/отступов; сохранить review/PR424 без новых требований. |
| [#425](https://github.com/sachkov-inside/platform/issues/425) Дать автору выбор закреплённого руководства главной | Уточнены требования; обновлено название | Целевая сущность после #448 — руководство: закреп выбирает одно руководство, не Material и не главу. |
| [#436](https://github.com/sachkov-inside/platform/issues/436) Реализовать общий Notifications, настройки каналов и email-доставку | Уточнены требования | Общий Notifications остаётся общей инфраструктурой. |
| [#437](https://github.com/sachkov-inside/platform/issues/437) Уведомлять о первой публикации материала и дать настройки каналов | Уточнены требования | First publication identity остаётся Material, а не каждый placement в руководстве: включение одного Material в несколько руководств, rename/migration/reorder не создаёт повторный анонс. |
| [#438](https://github.com/sachkov-inside/platform/issues/438) Проверить оба источника Notifications через RabbitMQ и Telegram/email | Уточнены требования | Дополнить corpus Billing one-off Guide purchase и MaterialPublished с subscriber/guide-only/overlapping grants. |
| [#443](https://github.com/sachkov-inside/platform/issues/443) Реализовать карточки терминов и связанный словарь для материалов из Obsidian | Уточнены требования | Определения переиспользуются между материалами и руководствами; «руководство» не превращается в Format guide. |
| [#444](https://github.com/sachkov-inside/platform/issues/444) Полный процесс работы с видео: Kinescope, агент, таймкоды и обложки | Уточнены требования | Во всех новых описаниях и пакетах порядок относится к руководству; #448 владеет общей миграцией Series references. |
| [#445](https://github.com/sachkov-inside/platform/issues/445) Видео через MCP и ссылки на конкретный момент | Сохранена без изменения | Активный ограниченный этап MCP Video и #t ссылок сохраняется; не превращать video chapters в главы руководства. |

## Сохранённая работа и границы

- #425 / PR #427: закреп и отдельное редактирование; сохраняются review и writing owner.
  Миграция #448 переносит итоговые ID/settings, не требует переписывать чужой worktree.
- #330 / PR #360 и #331 / PR #363: текущие открытия, resume и персональный UI сохраняются.
  Новая модель совместимости не означает, что уже проверены guide-only права.
- #421 / PR #422 и #423 / PR #424: текущие доменные и визуальные изменения не получают
  искусственного blocker на коммерческие решения. Миграция проверяет их итоговую совместимость.
- #444 сохраняет полный видеопроцесс; активная #445 выполняет только MCP Video и ссылки #t.
  Главы видео не являются главами руководства. Новая координационная сессия не забирает claim.
- #273/#274/#278/#279/#281/#282/#283: Мастерская остаётся отложенной; её Track и лаборатории
  не конвертируются. Не удалять прототипы, исходники, задачи или доказательства.
- #178/#184/#390 и #355: сохраняются точные границы старой media/production-приёмки.
  Новые scoped access и продажи не считаются проверенными прежним public/member smoke.
- Закрытые #403–#406 и предыдущие protocol snapshots остаются историей принятых поставок.
  Существующие course/manual/lifetime/legacy права не отзываются из-за нового имени продукта.

Связанные Workspace #110/#111/#126/#148/#149/#153, Content #1 и Telegram #55 получили
согласованные уточнения в своих границах. Human Backlog остаётся в Project 2; новые delivery
issues — в Project 1. Базовый Notifications #436 может выполняться по действующему нейтральному
контракту; новые purchase schemas и аудитория подключаются собственными producer tasks.

## Как продолжить

Первый технический исполнитель берёт Platform #447 после принятия документа #157 и получает
собственный start receipt. Затем #448 и Content #8 переносят платформу и оригиналы по одному
контракту. Workspace #158 и #159 можно обсуждать и готовить одновременно с техническим планом;
ожидание цены или чата не мешает описать и проверить миграцию Series.

На каждом старте проверить live issue, native blockers, session receipt, PR/head и рабочие
деревья: приведённый список не является бессрочным разрешением занять задачу. В этой поставке
не включено автоматическое закрытие aggregate; приёмка остаётся явной.
