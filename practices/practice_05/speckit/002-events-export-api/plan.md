# Implementation Plan: Экспорт событий в JSON

**Branch**: `002-events-export-api` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-events-export-api/spec.md` and shared contract `/specs/events-export-contract.md`.

## Summary

Добавить `GET /events/export` перед маршрутом `:id`. Сервис получает события и планеты из MongoDB, проверяет лимит 10 000, сортирует записи и возвращает строго заданный JSON с UTC-заголовками скачивания. Для GET-экспорта глобальный `AdminGuard` должен выполнять явную проверку сессии и роли ADMIN через metadata-декоратор маршрута.

## Technical Context

**Language/Version**: TypeScript, Node.js, NestJS 11

**Primary Dependencies**: `@nestjs/common`, `@nestjs/mongoose`, Mongoose, Jest, Supertest

**Storage**: MongoDB через Mongoose-модели `Event` и `Planet`

**Testing**: Jest, Supertest; обязательные `npx jest` и `npm run build` в `server/`

**Target Platform**: Linux server

**Project Type**: NestJS web service

**Performance Goals**: Экспорт до 10 000 событий одним запросом; при превышении сразу 413 без тела файла

**Constraints**: Только `server/`; без новых зависимостей; UTF-8 JSON, точные поля и порядок из общего контракта; ошибки NestJS без частичного ответа

**Scale/Scope**: Один endpoint, один сервисный метод, metadata-проверка для исключительного GET-маршрута и интеграционные тесты

## Constitution Check

- **I. Single Source of Truth**: PASS. Используются существующие коллекции MongoDB, новые хранилища не добавляются.
- **II. Admin-Only Writes and Sensitive Reads**: PASS. Экспорт помечается metadata и проходит ту же проверку сессии и роли ADMIN, что и защищённые записи.
- **III. Validated Input**: PASS. Endpoint не принимает параметры или тело, DTO не требуется.
- **IV. Same-Origin Client**: PASS. Маршрут остаётся NestJS endpoint под существующим rewrite `/api/backend`.
- **V. Minimal Change**: PASS. Меняются только auth metadata/guard, events controller/service и тесты.

## Project Structure

```text
server/src/
├── auth/admin.guard.ts
├── auth/admin.decorator.ts
├── events/event.controller.ts
├── events/event.service.ts
└── events/event-export.spec.ts
```

**Structure Decision**: Используется существующая NestJS структура `server/src`; экспорт реализуется в текущих controller/service, auth metadata выносится в небольшой декоратор, тесты размещаются рядом с модулем событий.

## Complexity Tracking

Нарушений конституции нет.
