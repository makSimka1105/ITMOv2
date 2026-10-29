# Tasks: Экспорт событий в JSON (UI)

**Input**: Design documents from `/specs/001-events-export-ui/`

**Prerequisites**: plan.md, spec.md, `specs/events-export-contract.md`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Проверить существующие `api`, `apiErrorMessage`, `useIsAdmin` и toast helper в `client/lib/api.ts`, `client/hooks/useIsAdmin.ts`, `client/components`

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 Сопоставить UI-обработку статусов, JSON-ответа и имени файла с `specs/events-export-contract.md`

## Phase 3: User Story 1 - Скачать все события карты (Priority: P1)

**Goal**: Администратор запускает экспорт одной кнопкой и получает JSON-файл.

**Independent Test**: В сессии ADMIN нажать кнопку и проверить GET-запрос, loading, имя файла и скачивание.

- [x] T003 [US1] Добавить кнопку «Экспорт событий» рядом с admin actions в `client/components/search/tabletControls.tsx`
- [x] T004 [US1] Реализовать GET `/events/export` через `api` с `responseType: "blob"` и блокировкой повторных кликов в `client/components/search/tabletControls.tsx`
- [x] T005 [US1] Проверить JSON-поля `exportedAt` и `events`, создать скачивание и разобрать `Content-Disposition` с fallback `events.json` в `client/components/search/tabletControls.tsx`
- [x] T006 [US1] Показать success toast «События успешно экспортированы» и вернуть кнопку в idle в `client/components/search/tabletControls.tsx`

## Phase 4: User Story 2 - Понятно обработать отсутствие событий (Priority: P2)

**Goal**: Пустой экспорт скачивается как валидный файл и объясняется пользователю.

**Independent Test**: Ответ `200` с `events: []` скачивает файл и показывает «События отсутствуют».

- [x] T007 [US2] Обработать пустой массив событий отдельным toast «События отсутствуют» в `client/components/search/tabletControls.tsx`

## Phase 5: User Story 3 - Показать ошибку экспорта (Priority: P2)

**Goal**: Ошибки получают contract-defined сообщения, а экспорт можно повторить.

**Independent Test**: Проверить 401/403, 413, сетевую ошибку, невалидный JSON и 5xx; после каждого сценария кнопка доступна.

- [x] T008 [US3] Добавить специальный toast для 413 и использовать `apiErrorMessage` для 401/403 и прочих ошибок в `client/components/search/tabletControls.tsx`
- [x] T009 [US3] Завершать loading через `finally` после любой ошибки в `client/components/search/tabletControls.tsx`

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T010 Запустить `npx tsc --noEmit` и `npm run build` в `client/`

## Dependencies & Execution Order

T001 → T002 → T003–T006 → T007–T009 → T010. User Story 2 и User Story 3 используют обработчик US1 и завершают его contract-specific ветвлениями.

## Parallel Opportunities

T003 и подготовку требований T002 можно выполнять отдельно до интеграции; проверки статусов T008 и loading cleanup T009 независимы по логике, но меняют один файл и выполняются последовательно.

## Implementation Strategy

MVP: завершить Phase 1–3 и проверить основной экспорт. Затем добавить пустой результат и ошибки, после чего выполнить обе quality gates.

