# Implementation Plan: Экспорт событий в JSON (UI)

**Branch**: `001-events-export-ui` | **Date**: 2026-10-29 | **Spec**: [spec.md](./spec.md)

## Summary

Добавить в панель управления кнопку «Экспорт событий», видимую только для роли `ADMIN`. Клиент отправляет через существующий Axios `api` запрос `GET /events/export` с `responseType: "blob"`, проверяет JSON-контракт, скачивает файл с именем из `Content-Disposition` или `events.json`, показывает contract-defined toast и всегда снимает состояние loading.

## Technical Context

**Language/Version**: TypeScript, React 19, Next.js 15

**Primary Dependencies**: существующие `axios`, `sonner`, React hooks

**Storage**: N/A, экспорт формируется сервером

**Testing**: `npx tsc --noEmit`, `npm run build` в `client/`

**Target Platform**: браузер через Next.js client application

**Project Type**: web application, frontend-only change

**Performance Goals**: один запрос на клик, без повторных запросов во время loading

**Constraints**: same-origin API через существующий `api`, без новых зависимостей, изменения только в `client/`

**Scale/Scope**: одна кнопка и обработчик экспорта в `TabletControls`

## Constitution Check

- I. Single Source of Truth: PASS. Клиент не хранит и не дублирует события.
- II. Admin-Only Writes and Sensitive Reads: PASS. Кнопка скрыта через `useIsAdmin()`; серверная авторизация остаётся обязательной.
- III. Validated Input: PASS. Ответ проверяется на `exportedAt` и массив `events`; ошибки показываются через `apiErrorMessage`.
- IV. Same-Origin Client: PASS. Используется существующий `api` с базовым путём `/api/backend` и cookie.
- V. Minimal Change: PASS. Меняется только `client/components/search/tabletControls.tsx`, зависимости не добавляются.

Все quality gates клиента выполняются командами из задания.

## Project Structure

```text
specs/001-events-export-ui/
├── plan.md
├── spec.md
└── tasks.md

client/components/search/
└── tabletControls.tsx
```

**Structure Decision**: существующий Next.js client component остаётся единственной точкой интеграции рядом с другими admin actions. Общий API helper и toast library переиспользуются.

## Design

Обработчик блокирует повторный клик флагом loading, запрашивает blob, декодирует и валидирует JSON, затем создаёт временную ссылку для скачивания. Статусы 401/403 и прочие сообщения проходят через `apiErrorMessage`; 413 получает отдельный toast. В блоке `finally` кнопка возвращается в idle.

## Post-Design Constitution Check

Все пять принципов сохраняются: состояние не дублируется, доступ ограничен UI и сервером, ответ валидируется, запрос same-origin, изменение локально и использует существующие зависимости.

