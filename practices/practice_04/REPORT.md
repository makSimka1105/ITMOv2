# Практика 4: среда агента, skill и собственный MCP

Проект: warhammerMap, интерактивная карта галактики WH40k для ролевого сообщества (Next.js 15 + NestJS 11 + MongoDB). Агент: Claude Code. Репозиторий проекта: https://github.com/makSimka1105/warhammerMap/tree/course/agents-workflow

Что лежит в этой папке:

- `agent-env/` снимок среды из проекта: `AGENTS.md`, `.mcp.json`, `.claude/settings.json` (hook), `.claude/hooks/check-edit.sh`, `.claude/skills/smoke-api/SKILL.md`;
- `mcp/image-refs/` собственный MCP-сервер (в проекте лежит по тому же пути `mcp/image-refs/`);
- `evidence/` подтверждения: вызовы MCP, прогоны hook и smoke-api, полный лог агентного прогона `agent-run.jsonl` и дифф его правок `agent-fix.diff`;
- `reflection.md`.

## Среда

| Что | Файл | Зачем |
|---|---|---|
| Правила | `agent-env/AGENTS.md` | Архитектура «одна Mongo на всё», поток запросов через прокси Next, env, таблица API, конвенции и проверки. Это то, что не выводится из кода за один проход: почему нельзя заводить второе хранилище и почему клиент не ходит в Nest напрямую. |
| Skill | `agent-env/.claude/skills/smoke-api/SKILL.md` | Проверка API от трёх ролей (anonymous / user / admin) через тот же прокси, что и браузер. jest не покрывает guard вместе с прокси и cookie, а skill покрывает. |
| MCP, готовый | `agent-env/.mcp.json` → `mongodb-mcp-server@3.0.5`, `MDB_MCP_READ_ONLY=true` | Смотреть данные без самописных скриптов, без права на запись. |
| MCP, свой | `agent-env/.mcp.json` → `mcp/image-refs/server.js` | Целостность GridFS: файлы без ссылок и ссылки на несуществующие файлы (см. ниже). |
| Hook | `agent-env/.claude/settings.json` (PostToolUse на Edit/Write/MultiEdit) → `agent-env/.claude/hooks/check-edit.sh` | После каждой правки TS-файла typecheck пакета и запрет голого `axios` в клиенте. При exit 2 stderr уходит агенту. |
| Runner | `tsc --noEmit`, `npm test` (jest), `npm run build` в `server/` и `client/`; dev Mongo `docker-compose.dev.yml` | Команды из раздела Checks в AGENTS.md. |

Фичи практики делались по схеме A, затем B в отдельной ветке-worktree, затем merge: `feature/upload-hardening`, `feature/server-prod`, `feature/client-prod` (см. `git log`, 2026-10-02).

## Hook: реальный прогон

`evidence/hook-runs.txt`. На клиентский файл с голым `import axios` и ошибкой типа hook вернул exit 2 и оба замечания:

```
client/components/hookDemo.ts imports axios directly. Use { api } from "@/lib/api" so requests carry the session cookie.
tsc failed in client/:
components/hookDemo.ts(4,14): error TS2322: Type 'string' is not assignable to type 'number'.
exit=2
```

На чистом `server/src/files/file.service.ts` hook вернул exit 0. Hook не проверяет файлы вне `client/` и `server/src/` и не запускает jest: на каждую правку это слишком долго, jest остаётся в Checks.

## Skill smoke-api: устройство и запуск

Устройство: три шага. (1) Регистрация и вход двух пользователей с сохранением cookie в jar-файлы. Роль ADMIN выдаётся по `ADMIN_EMAILS` только при регистрации. (2) Каждый изменённый endpoint дёргается от anonymous, user и admin, ожидаются 401 / 403 / 2xx, а картинки из ответа должны отдаваться через `/api/backend/files/<name>` с `image/*`. (3) Уборка через DELETE и проверка через read-only MCP, что строк и файлов не осталось. Критерий готовности записан в последней строке skill, поэтому агент не может объявить «готово» раньше уборки.

Запуск на локальном стеке (`evidence/smoke-api-run.txt`):

| Запрос | anon | user | admin |
|---|---:|---:|---:|
| POST /legions (png) | 401 | 403 | 201 |
| POST /legions (text/plain) | | | 400 |
| DELETE /legions/:id | 401 | 403 | 200 |

После создания `GET /files/<icon>` отдал `200 image/png`, после удаления `404`. Проверка уборки (`evidence/mcp-after-smoke.txt`): `image_refs` вернул `files: 0, orphans: [], dangling: []`, `find` из mongodb MCP по `legions` и `images.files` вернул 0 документов.

Что пришлось исправить в skill по итогам запуска: `find` в mongodb-mcp-server 3.x без `connectionId` падает с `Input validation error: ... connectionId: Invalid input: expected string, received undefined`. В шаг 3 добавлен `connectionId: "preconfigured"` и проверка через `image_refs`. То же уточнение внесено в AGENTS.md.

## Собственный MCP: image-refs

`mcp/image-refs/server.js`, stdio, `@modelcontextprotocol/sdk` 1.32 + драйвер `mongodb`. Один tool `image_refs`, `readOnlyHint: true`.

Зачем: в AGENTS.md в «Known problems» записано, что успешный upload с последующим упавшим insert оставляет осиротевший файл в GridFS. Готовый mongodb MCP умеет только `find` по одной коллекции, и чтобы найти сирот, агенту пришлось бы руками сопоставлять `images.files` с `planets.pic`, `legions.icon` и `events.shots`. `image_refs` делает это одним вызовом:

- без аргументов: `orphans` (файлы, на которые никто не ссылается) и `dangling` (ссылки на отсутствующие файлы);
- с `name`: кто ссылается на конкретный файл и существует ли он.

Вызовы через MCP Inspector CLI (`evidence/image-refs-calls.txt`) на фикстуре из файла-иконки легиона, файла без ссылок и планеты с битой ссылкой:

| Сценарий | Результат |
|---|---|
| без аргументов | `files: 2, references: 2`, в `orphans` файл без ссылок, в `dangling` `planets/... (Smoke Planet).pic` |
| `name=6ac673d50f57dcfdb6122bb6.png` | `exists: true`, `referencedBy: ["legions/... (Smoke Legion).icon"]` |
| `name=../etc/passwd` | `isError: true`, `"../etc/passwd" is not a stored image name. Expected <24 hex objectId>.<png\|jpg\|webp>` |
| Mongo недоступна | `isError: true`, `MongoDB unavailable: connect ECONNREFUSED 127.0.0.1:27999` |

Первая версия на недоступной Mongo отвечала `Topology is closed`, и по этому тексту агент не понял бы, что делать. Явный `client.connect()` в обработчике дал понятную причину.

## Всё вместе в реальной задаче

Один headless-прогон Claude Code (sonnet, `claude -p` с `--mcp-config .mcp.json`, без права на commit/push, лимит $3, потрачено $0.33). Полный лог в `evidence/agent-run.jsonl`, дифф правок в `evidence/agent-fix.diff`. Задача: закрыть пункт «orphan GridFS file» из Known problems.

Последовательность вызовов из лога:

1. `ToolSearch` подгружает `mcp__image-refs__image_refs` и `mcp__mongodb__find`.
2. `image_refs {}` фиксирует исходное состояние: `files: 0, orphans: [], dangling: []`.
3. Read трёх сервисов и `file.service.ts`, Edit `create` в `planets.service.ts`, `legion.service.ts`, `event.service.ts`: insert обёрнут в try/catch, при ошибке `deleteFile`/`deleteFiles`, исходная ошибка пробрасывается.
4. Write `server/src/files/create-cleanup.spec.ts` (три теста на моках), затем `tsc --noEmit && npm test && npm run build`: 19/19.
5. `Skill smoke-api` и его шаги curl'ом: POST/DELETE `/legions` дали 401 / 403 / 2xx.
6. `image_refs {}` и `mongodb find {connectionId: "preconfigured", collection: "legions"}` подтверждают уборку. `connectionId` агент взял из исправленного skill.
7. Edit AGENTS.md: пункт из Known problems удалён.

AGENTS.md агент отдельно не читал: Claude Code загружает его в контекст сам. Это видно по тому, что `Edit` по AGENTS.md прошёл без предварительного `Read`, а spec-файл и `connectionId` оформлены по его правилам. Hook срабатывал после каждой Edit/Write, но во всех случаях с exit 0. События PostToolUse в stream-json не попадают, поэтому в логе их не видно; срабатывание с ошибкой показано выше в `evidence/hook-runs.txt`.

Агент сам сообщил, что smoke-api прошёл на старом коде: Nest был запущен до его сборки, а перезапускать чужой процесс он не стал. После отчёта я перезапустил Nest и повторил проверку на новом билде (`evidence/smoke-api-after-fix.txt`): те же статусы по ролям, `image_refs` пуст, `npm test` 3 suites / 19 tests passed.

Ещё агент нашёл за рамками задачи два оставшихся источника сирот: частичный сбой `uploadFiles` (`Promise.all`) и упавший `legion.save()` после insert планеты. При этом пункт из Known problems он удалил целиком. Я вернул его в уточнённом виде: что закрыто, что осталось и что `image_refs` находит такие файлы.
