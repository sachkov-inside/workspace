# Бесплатные code-intelligence tools и MCP для Inside

Дата проверки: 2026-08-19.

> Runtime boundary updated later the same day: user-level Serena, Docker MCP and Graphify
> integrations were retired. Any future use described below is project-owned and must not assume
> device registration.

## Критерий

Обязательная часть product harness должна работать без платной подписки, биллинга и обязательного
платного API. Open-source клиент поверх freemium SaaS не считается полностью бесплатной базовой
зависимостью. Такой сервис допустим только как явно опциональный free-tier, если при исчерпании
лимита он блокируется без автоматических списаний.

## Решение на текущем этапе

Не добавлять новые обязательные MCP в product harness. Platform пока не содержит кодовой базы, а
Landing достаточно мал и уже обслуживается native file, search, shell и `playwright-cli` tools.
Дополнительные always-on servers сейчас увеличат startup cost, context/tool noise и поверхность
доступа сильнее, чем пользу.

| Tool | Бесплатность | Польза | Решение сейчас |
| --- | --- | --- | --- |
| [Serena](https://github.com/oraios/serena) | MIT; LSP backend бесплатен, JetBrains backend платный | Live symbol navigation, references, diagnostics и semantic edits | Не добавлять сейчас; при доказанной нужде подключить только в project harness |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Code-only работает локально; repository содержит MIT/Apache license files | Статический knowledge graph по code/docs | Не ставить; вернуться при реальной большой multi-repo архитектуре |
| [Context7](https://github.com/upstash/context7) | MIT MCP client, но hosted freemium service | Актуальная version-specific документация библиотек | Не делать обязательным; optional только если free-tier считается допустимым |
| [GitHub MCP](https://github.com/github/github-mcp-server) | MIT server; GitHub account/API limits остаются | Issues, PR, Actions и releases | Позже, после выбора GitHub как task tracker и collaboration surface |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Apache-2.0, local | Browser automation через MCP tools | Не нужен: общий harness уже содержит `playwright-cli` skill и CLI |
| [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) | Apache-2.0, local | Network, performance, console и runtime debugging | Только on-demand позже, если Playwright CLI не покрывает конкретную задачу |

## Serena

Serena закрывает реальный пробел native tools: symbol-level search, references, diagnostics и
semantic editing. Бесплатный LSP backend поддерживает C#, TypeScript, JavaScript, HTML и CSS.
Serena официально интегрируется через MCP и рекомендует устанавливать её по собственному Quick
Start, а не из marketplace. Источник: [Serena README](https://github.com/oraios/serena#the-ide-for-your-coding-agent).

Исторический device-wide pilot выявил:

- 19 процессов `serena-agent start-mcp-server`, 49 language-server процессов и один dashboard;
- процессы живут от нескольких часов до нескольких дней;
- wrapper синхронизирует `.serena/project.yml` даже при вызове `serena --version`;
- committed Landing config содержит только `bash`, хотя приложение использует Astro/TypeScript;
- Serena уже создавала лишний `.serena` state в Workspace при обычном agent run.

User-level registrations после пилота сняты. Если вернуться к Serena:

1. Зарегистрировать Serena project-local, а не в user scope.
2. Использовать только бесплатный LSP backend и pinned release.
3. Оставить только symbol navigation, references, diagnostics и semantic refactoring; отключить
   дублирующие file, shell и memory tools, dashboard и prompt overrides.
4. Явно определить lifecycle `.serena/project.yml` и local state.
5. Провести пилот в одном непустом code repository и измерить пользу до распространения.

## Graphify

Graphify не заменяет Serena. Serena работает с живым кодом через LSP, а Graphify строит отдельный
snapshot graph для архитектурных запросов. Code-only extraction выполняется локально через
tree-sitter, без LLM и vector store; semantic processing docs и media использует модель агента или
настроенный backend. Источник: [Graphify README](https://github.com/Graphify-Labs/graphify#readme).

Сейчас overhead преждевременный: создаётся `graphify-out/`, graph нужно обновлять, а штатный
installer пишет skills, `AGENTS.md`, hooks и некоторые platform-specific integrations. Это
пересекается с ownership нашего harness. Если инструмент понадобится позже, использовать pinned
CLI в code-only режиме и интегрировать skill через canonical package, не запускать автоматический
platform installer.

## Context7

Context7 хорошо решает поиск актуальной документации, но не является полностью бесплатной
инфраструктурой:

- Free plan стоит $0 и включает 1000 API calls в месяц;
- после лимита Free блокируется и получает 20 bonus calls в день;
- private repositories доступны только на платных планах;
- self-hosted deployment относится к Enterprise.

Источники: [Context7 plans](https://context7.com/plans) и
[official repository](https://github.com/upstash/context7#readme).

Следовательно, Context7 нельзя делать обязательной частью product harness под строгий критерий
полной бесплатности. Его можно отдельно включить как opt-in free-tier без fallback-зависимости:
агент должен продолжать работу через official docs и `research`, если лимит исчерпан или сервис
недоступен.

## Какие MCP рассматривать дальше

### Общей базы нет

User-level Docker MCP gateway снят с Codex, Claude Code, Kimi и OpenCode. Для актуальной Docker и
.NET документации агент использует official web docs. Если частые задачи докажут пользу MCP,
конкретный repository добавляет reviewed project registration без дублирования в user scope.

### Позже по фактической потребности

- GitHub MCP: после решения использовать GitHub Issues/Projects/PR. Начинать с read-only и
  минимальных `repos`, `issues`, `pull_requests`, `actions` toolsets; credentials не хранить в Git.
- Database MCP: только когда появится БД, исключительно для local/dev и сначала read-only. Никогда
  не подключать production database как default agent tool.
- Chrome DevTools MCP: on-demand для performance/network диагностики, которую не покрывает
  Playwright CLI.

### Не добавлять

- `filesystem`, `git`, `fetch`: дублируют native agent tools;
- `memory`: создаёт второй источник product knowledge рядом с versioned docs;
- `sequential-thinking`: дублирует model reasoning и увеличивает context;
- Playwright MCP: дублирует установленный `playwright-cli`;
- Exa, Tavily, Firecrawl и аналогичные API MCP: не проходят критерий гарантированно бесплатной
  работы;
- database, Sentry и deployment MCP до появления соответствующей инфраструктуры и access policy.

Официальный набор reference servers также позиционирует Filesystem, Git, Fetch, Memory,
Sequential Thinking и Time как reference implementations, а не обязательный starter pack:
[modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers#readme).

## Как интегрировать MCP в harness, когда появится необходимость

1. Product Workspace может хранить reviewed templates: capability, source, pinned version, license,
   required permissions и бесплатность.
2. MCP включается только opt-in, отдельно от skills package.
3. Конкретный repository хранит native project configs нужных runtimes; установленный binary может
   быть device prerequisite, но не активной user-scope registration.
4. Secrets остаются в environment/native auth и никогда не попадают в repository.
5. Никаких `@latest`, floating Git branches, plugins или marketplace installers.
6. `health` проверяет version, connection, tool allow-list, process cleanup и отсутствие лишнего
   repository state.
7. Каждый новый server сначала проходит пилот в одном repository; затем принимается отдельное
   решение о product-wide распространении.
