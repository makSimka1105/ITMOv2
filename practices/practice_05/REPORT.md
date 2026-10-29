# Практика 5. Spec-driven development с OpenSpec

Проект: [warhammerMap, ветка practice-5-spec-driven](https://github.com/makSimka1105/warhammerMap/tree/practice-5-spec-driven). Здесь лежит снимок артефактов OpenSpec из этой ветки.

## Часть 1. User Story 3 через полный цикл

История: [user-story-3.md](user-story-3.md), редактирование события карты через `PUT /events/:id`.

| Шаг | Что сделано | Артефакт |
|---|---|---|
| Setup | `openspec init --profile core --tools opencode --language ru`, OpenSpec 1.14.1 | [config.yaml](openspec/config.yaml) |
| Explore и propose | proposal, delta spec с 4 требованиями, design, tasks; `openspec validate --strict` проходит | [change](openspec/changes/archive/2026-10-29-add-event-edit/) |
| Review | отдельный агент opencode `plan` нашёл 10 пробелов: `null` обходил валидацию, связь чистилась только у старой планеты, тесты не воспроизводили production pipe и другие; все решения внесены в spec и design | [review.md](openspec/changes/archive/2026-10-29-add-event-edit/evidence/review.md) |
| Apply | явный `UpdateEventDto` с `@ValidateIf`, `$pull` из всех прочих планет и `$addToSet` в текущую, тесты на частичное изменение, рассинхрон, 404 и DTO | коммит `feat(server)` в ветке проекта |
| Verify | независимая проверка нашла баг: с `ValidationPipe({ transform: true })` PUT стирал неотправленные поля, а перенос без `name` давал 500. Исправлено, тесты гоняют сервис через тот же pipe и падают без фикса | [verify.md](openspec/changes/archive/2026-10-29-add-event-edit/evidence/verify.md), [verify-2.md](openspec/changes/archive/2026-10-29-add-event-edit/evidence/verify-2.md) |
| Archive | главная спека обновлена, change в архиве | [specs/events/spec.md](openspec/specs/events/spec.md) |

Итог проверок: `npx jest` 38 passed, `npx tsc --noEmit` без ошибок, все сценарии спеки подтверждены HTTP-запросами через production pipe.

## Часть 2. Правило проекта

В `openspec/config.yaml` добавлено `rules.design: Объясни взаимодействие диаграммой Mermaid`, `openspec instructions design` возвращает его в `rules`. Правило проверено на следующем связанном change `add-event-edit-ui` (редактирование события в админ-панели), design до правила, после правила с sequence-диаграммой и diff. Затем change доведён до apply: в админ-панели у события есть кнопка «изменить», форма с выбором планеты переносит событие между планетами. Сценарии спеки проверены в браузере, change заархивирован, главная спека [event-admin-ui](openspec/specs/event-admin-ui/spec.md).

- [design-before.md](openspec/changes/archive/2026-10-29-add-event-edit-ui/evidence/design-before.md)
- [design.md](openspec/changes/archive/2026-10-29-add-event-edit-ui/design.md)
- [design.diff](openspec/changes/archive/2026-10-29-add-event-edit-ui/evidence/design.diff)

## Выводы

Спека до кода окупилась на проверке: требование «неотправленные поля MUST сохраняться» дало конкретный сценарий, по которому независимый агент нашёл потерю данных, хотя тесты автора проходили. Без записанного сценария этот баг ушёл бы в production.

Полезнее всего оказалось разделение ролей: автор пишет код, отдельный агент без права записи проверяет спеку до кода и результат после, а решение о приёмке остаётся за человеком. Отчёт автора проверкой не считается.
