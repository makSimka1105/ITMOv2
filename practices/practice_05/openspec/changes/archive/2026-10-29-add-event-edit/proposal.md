# Proposal

## Why

Событие на карте нельзя исправить: API умеет только создавать и удалять события. Чтобы поменять опечатку в названии или перенести событие на другую планету, администратор удаляет событие и создаёт его заново, теряя загруженные снимки.

## What Changes

- Новый эндпоинт `PUT /events/:id`: частичное изменение `name`, `description`, `link` и `place`.
- При смене `place` событие убирается из списка `events` старой планеты и добавляется в список новой.
- Снимки (`shots`) при редактировании не меняются.
- Строка таблицы API в `README.md` дополняется методом PUT.

Не входит в изменение: замена и удаление снимков, редактирование событий в клиенте.

## Capabilities

### New Capabilities
- `events`: управление событиями карты и их связью с планетами.

### Modified Capabilities

## Impact

- `server/src/events/event.controller.ts`, `server/src/events/event.service.ts`
- новый `server/src/dto/update-event.dto.ts` на основе `CreateEventDto`
- `server/src/integrity.spec.ts`: интеграционные тесты против MongoDB
- клиент и схема данных не меняются
