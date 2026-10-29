# Design

## Context

Создание события идёт через `EventCreateDrawer` и thunk `createEvent`, который отправляет `FormData`. Сервер принимает `PUT /events/:id` только как JSON и не меняет снимки. После мутаций слайс перезагружает список планет вместе с событиями.

## Goals / Non-Goals

**Goals:**
- редактировать событие из той же карточки планеты, где его создают и удаляют

**Non-Goals:**
- редактирование снимков

## Decisions

- Отдельный `EventEditDrawer`, а не режим `EventCreateDrawer`: в форме создания есть загрузка снимков и `FormData`, в форме редактирования их нет, общий компонент держал бы две ветки поведения.
- `updateEvent` отправляет JSON, потому что `PUT /events/:id` не разбирает multipart.
- После успешного `updateEvent` вызывается та же перезагрузка планет, что после `createEvent`: перенос события меняет хронику двух планет сразу.

## Interaction

```mermaid
sequenceDiagram
    actor Admin
    participant Drawer as EventEditDrawer
    participant Slice as planetSlices
    participant API as PUT /events/:id
    participant DB as MongoDB
    Admin->>Drawer: меняет поля и планету, сохраняет
    Drawer->>Slice: dispatch(updateEvent)
    Slice->>API: JSON name, description, link, place
    API->>DB: сохранить событие
    API->>DB: $pull из прочих планет, $addToSet в текущую
    alt 200
        API-->>Slice: обновлённое событие
        Slice->>API: перезагрузка планет
        Slice-->>Drawer: успех, форма закрывается
    else 400 или 404
        API-->>Slice: ошибка
        Slice-->>Drawer: rejectWithValue, форма остаётся открытой с сообщением
    end
```

## Risks / Trade-offs

- [Перезагрузка всех планет после каждого изменения] → объём данных карты небольшой, тот же подход уже используется для создания и удаления.
