# Tasks: Экспорт событий в JSON

**Input**: Design documents from `/specs/002-events-export-api/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), shared contract `/specs/events-export-contract.md`

## Phase 1: Setup

- [x] T001 Проверить существующие NestJS-маршруты событий и глобальный `AdminGuard` в `server/src/events/event.controller.ts` и `server/src/auth/admin.guard.ts`

## Phase 2: Foundational

- [x] T002 [P] Добавить metadata-декоратор обязательной admin-проверки в `server/src/auth/admin.decorator.ts`
- [x] T003 Изменить `server/src/auth/admin.guard.ts`, чтобы GET с metadata проходил проверку cookie/session/role, а остальные GET сохраняли текущее поведение

## Phase 3: User Story 1 - Полный экспорт администратора (P1) 🎯 MVP

**Goal**: ADMIN получает валидный JSON-файл со всеми событиями, связанными данными планет, стабильной сортировкой и лимитом 10 000.

**Independent Test**: `GET /events/export` с ADMIN возвращает 200, точные заголовки и тело контракта; события отсортированы, `place` раскрыт или равен `null`, при 10 001 событии возвращается 413.

- [x] T004 [P] [US1] Добавить тесты порядка, сохранения `shots`, раскрытия полей планеты и `place: null` в `server/src/events/event-export.spec.ts`
- [x] T005 [P] [US1] Добавить тесты 413 при 10 001 событии и явной защиты GET без cookie/с ролью USER в `server/src/events/event-export.spec.ts`
- [x] T006 [US1] Реализовать метод экспорта, сортировку, нормализацию полей, проверку лимита и преобразование ошибок в `server/src/events/event.service.ts`
- [x] T007 [US1] Объявить `GET /events/export` перед `@Get(':id')`, применить admin metadata и выставить контрактные заголовки в `server/src/events/event.controller.ts`

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T008 Запустить `npx jest` и `npm run build` в `server/`, исправить найденные ошибки и подтвердить формат задач/контракта

## Dependencies & Execution Order

- Phase 1 предшествует Phase 2.
- Phase 2 блокирует User Story 1.
- В User Story 1 тесты T004-T005 могут быть написаны параллельно, реализация T006-T007 зависит от их контракта.
- T008 выполняется после всех изменений.

## Parallel Opportunities

- T002 и подготовка тестовых сценариев T004-T005 затрагивают разные файлы и могут выполняться параллельно.
- Внутри US1 тесты сортировки и авторизации независимы.

## Implementation Strategy

Сначала сохранить существующее поведение глобального guard для обычных GET, затем добавить исключительный metadata-маршрут экспорта и сервисный формат ответа. MVP полностью покрывает US1, включая ошибки доступа и лимита, после чего выполняются общие проверки сборки и тестов.
