# Повторная проверка после исправления

Собранный `dist`, `ObjectModule` с `ValidationPipe({ whitelist: true, transform: true })` как в `main.ts`, реальные HTTP-запросы против MongoDB.

```
created {"name":"Hunt","description":"Old","link":"https://example.invalid/hunt","place":"6ae2842a1250dc59e707ab90","shots":["6ae2842a1250dc59e707ab9b.png"]}
1. partial: only name
  PUT /events/6ae2842a1250dc59e707ab9d {"name":"Great Hunt"}
  -> 200 {"name":"Great Hunt","description":"Old","link":"https://example.invalid/hunt","place":"6ae2842a1250dc59e707ab90","shots":["6ae2842a1250dc59e707ab9b.png"]}
   GET after
  GET /events/6ae2842a1250dc59e707ab9d ""
  -> 200 {"name":"Great Hunt","description":"Old","link":"https://example.invalid/hunt","place":"6ae2842a1250dc59e707ab90","shots":["6ae2842a1250dc59e707ab9b.png"]}
2. move: description + place, shots sent
  PUT /events/6ae2842a1250dc59e707ab9d {"description":"Updated","place":"6ae2842a1250dc59e707ab96","shots":["hacked.png"]}
  -> 200 {"name":"Great Hunt","description":"Updated","link":"https://example.invalid/hunt","place":"6ae2842a1250dc59e707ab96","shots":["6ae2842a1250dc59e707ab9b.png"]}
   first.events []
   second.events ["6ae2842a1250dc59e707ab9d"]
   integrity issues []
3. invalid
  PUT /events/6ae2842a1250dc59e707ab9d {"name":""}
  -> 400 ["name should not be empty"]
3. invalid
  PUT /events/6ae2842a1250dc59e707ab9d {"name":null}
  -> 400 ["name should not be empty","name must be a string"]
3. invalid
  PUT /events/6ae2842a1250dc59e707ab9d {"place":null}
  -> 400 ["place must be a mongodb id"]
3. invalid
  PUT /events/6ae2842a1250dc59e707ab9d {"place":"not-an-id"}
  -> 400 ["place must be a mongodb id"]
4. unknown event
  PUT /events/0123456789abcdef01234567 {"name":"Ghost"}
  -> 404 "Object with id 0123456789abcdef01234567 not found"
5. unknown planet
  PUT /events/6ae2842a1250dc59e707ab9d {"place":"0123456789abcdef01234567"}
  -> 404 "Planet 0123456789abcdef01234567 not found"
   GET final
  GET /events/6ae2842a1250dc59e707ab9d ""
  -> 200 {"name":"Great Hunt","description":"Updated","link":"https://example.invalid/hunt","place":"6ae2842a1250dc59e707ab96","shots":["6ae2842a1250dc59e707ab9b.png"]}
```

`npx jest`: 38 passed. `npx tsc --noEmit`: без ошибок.
