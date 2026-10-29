
> plan · deepseek/deepseek-v4.1-flash-1017
I'll start by reading the spec and checking the repo state.
→ Read openspec/changes/add-event-edit/specs/events/spec.md 
$ cd /home/maksibon/projects/warhammerMap && git status --short && git diff --stat
M README.md
 M server/src/events/event.controller.ts
 M server/src/events/event.service.ts
 M server/src/integrity.spec.ts
?? .opencode/
?? openspec/
?? server/src/dto/update-event.dto.spec.ts
?? server/src/dto/update-event.dto.ts
?? specs/
 README.md                             |  2 +-
 server/src/events/event.controller.ts |  5 ++++
 server/src/events/event.service.ts    | 20 ++++++++++++++++
 server/src/integrity.spec.ts          | 43 ++++++++++++++++++++++++++++++++++-
 4 files changed, 68 insertions(+), 2 deletions(-)
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/src/dto/update-event.dto.spec.ts 
→ Read server/src/dto/update-event.dto.ts 
$ cd /home/maksibon/projects/warhammerMap && git diff
diff --git a/README.md b/README.md
index 26a9c38..005b65e 100644
--- a/README.md
+++ b/README.md
@@ -149,7 +149,7 @@ cd client && npx tsc --noEmit && npm run build
 | GET, POST | `/legions` | файл `icon` |
 | GET, PUT, DELETE | `/legions/:id` | удаление убирает легион со всех планет |
 | GET, POST | `/events` | до 4 файлов `shots`, `place` это id планеты |
-| GET, DELETE | `/events/:id` | |
+| GET, PUT, DELETE | `/events/:id` | PUT меняет поля события и переносит его на другую планету, снимки не трогает |
 | GET | `/files/:name` | изображение из GridFS с immutable-кэшем |
 
 ## Деплой
diff --git a/server/src/events/event.controller.ts b/server/src/events/event.controller.ts
index 020e1a7..20075fe 100644
--- a/server/src/events/event.controller.ts
+++ b/server/src/events/event.controller.ts
@@ -3,6 +3,7 @@ import { FileFieldsInterceptor } from "@nestjs/platform-express"
 import { ParseObjectIdPipe } from "src/common/parse-object-id.pipe";
 import { imageUploadOptions } from "src/files/upload.options"
 import { CreateEventDto } from "src/dto/create-event.dto"
+import { UpdateEventDto } from "src/dto/update-event.dto"
 import { EventService } from "./event.service"
 
 
@@ -28,6 +29,10 @@ export class EventController{
         return this.eventService.getOne(id)
         
     }
+    @Put(':id')
+    update(@Param('id', ParseObjectIdPipe) id: string, @Body() dto: UpdateEventDto) {
+        return this.eventService.update(id, dto)
+    }
     @Delete(':id')
     delete(@Param('id', ParseObjectIdPipe) id: string){
         return this.eventService.deleteOne(id)
diff --git a/server/src/events/event.service.ts b/server/src/events/event.service.ts
index d45b057..f37ae23 100644
--- a/server/src/events/event.service.ts
+++ b/server/src/events/event.service.ts
@@ -2,6 +2,7 @@ import { Injectable, NotFoundException } from "@nestjs/common";
 import { InjectModel } from "@nestjs/mongoose";
 import { Model } from "mongoose";
 import { CreateEventDto } from "src/dto/create-event.dto";
+import { UpdateEventDto } from "src/dto/update-event.dto";
 import { FileService } from "src/files/file.service";
 import { Planet, PlanetDocument } from "src/planets/planets.schema";
 import { Event, EventDocument } from "./event.schema";
@@ -49,6 +50,25 @@ export class EventService {
         return event!
     }
 
+    async update(id: string, dto: UpdateEventDto): Promise<Event> {
+        const event = await this.eventModel.findById(id).exec();
+        handleObjNotFound(event, id);
+
+        const nextPlace = dto.place ?? event!.place.toString();
+        const place = await this.planetModel.findById(nextPlace).exec();
+        if (!place) {
+            throw new NotFoundException(`Planet ${nextPlace} not found`);
+        }
+
+        Object.assign(event!, dto);
+        event!.place = place._id;
+        await event!.save();
+
+        await this.planetModel.updateMany({ events: event!._id, _id: { $ne: place._id } }, { $pull: { events: event!._id } });
+        await this.planetModel.updateOne({ _id: place._id }, { $addToSet: { events: event!._id } });
+        return event!;
+    }
+
     async deleteOne(id: string): Promise<{ id: string }> {
         const event = await this.eventModel.findByIdAndDelete(id).exec();
         handleObjNotFound(event, id)
diff --git a/server/src/integrity.spec.ts b/server/src/integrity.spec.ts
index de45fff..83c8ee7 100644
--- a/server/src/integrity.spec.ts
+++ b/server/src/integrity.spec.ts
@@ -1,7 +1,7 @@
 import { INestApplication } from '@nestjs/common';
 import { getConnectionToken, MongooseModule } from '@nestjs/mongoose';
 import { Test } from '@nestjs/testing';
-import { Connection } from 'mongoose';
+import { Connection, Types } from 'mongoose';
 import * as request from 'supertest';
 import { PlanetService } from 'src/planets/planets.service';
 import { ObjectModule } from 'src/objects.module';
@@ -122,6 +122,47 @@ describe('relations and images stay consistent', () => {
         expect(Object.keys(planet).sort()).toEqual(Object.keys(listed).sort());
     });
 
+    it('partial event update keeps the fields that were not sent', async () => {
+        const planet = await createPlanet('Fenris');
+        const event = (await http().post('/events').field('name', 'Hunt').field('description', 'Old')
+            .field('link', 'https://example.invalid/hunt').field('place', planet._id).expect(201)).body;
+
+        const updated = (await http().put(`/events/${event._id}`).send({ name: 'Great Hunt' }).expect(200)).body;
+
+        expect(updated).toMatchObject({ name: 'Great Hunt', description: 'Old', link: 'https://example.invalid/hunt', place: planet._id });
+        expect((await http().get(`/events/${event._id}`)).body).toEqual(updated);
+    });
+
+    it('updates an event and moves its planet relation', async () => {
+        const first = await createPlanet('First');
+        const second = await createPlanet('Second');
+        const stale = await createPlanet('Stale');
+        const event = (await http().post('/events').field('name', 'Landing').field('place', first._id)
+            .attach('shots', PNG, { filename: 's.png', contentType: 'image/png' }).expect(201)).body;
+        await connection.db!.collection('planets').updateOne({ name: 'Stale' }, { $set: { events: [new Types.ObjectId(event._id)] } });
+        const files = await countFiles();
+
+        const updated = (await http().put(`/events/${event._id}`).send({ description: 'Updated', place: second._id }).expect(200)).body;
+
+        expect(updated).toMatchObject({ name: 'Landing', description: 'Updated', place: second._id });
+        expect(updated.shots).toEqual(event.shots);
+        expect(await countFiles()).toBe(files);
+        expect((await http().get(`/planets/${first._id}`)).body.events).toEqual([]);
+        expect((await http().get(`/planets/${stale._id}`)).body.events).toEqual([]);
+        expect((await http().get(`/planets/${second._id}`)).body.events[0]._id).toBe(event._id);
+        expect(await issues()).toEqual([]);
+    });
+
+    it('answers 404 when updating an unknown event or moving it to an unknown planet', async () => {
+        const planet = await createPlanet('Terra');
+        const event = (await http().post('/events').field('name', 'Siege').field('place', planet._id).expect(201)).body;
+        const missing = '0123456789abcdef01234567';
+
+        await http().put(`/events/${missing}`).send({ name: 'Ghost' }).expect(404);
+        await http().put(`/events/${event._id}`).send({ place: missing }).expect(404);
+        expect((await http().get(`/events/${event._id}`)).body).toMatchObject({ name: 'Siege', place: planet._id });
+    });
+
     it('full lifecycle leaves no dangling refs or orphan files', async () => {
         const legion = await createLegion('Lions');
         const planet = await createPlanet('Caliban', { legion1: legion._id });
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/src/main.ts 
→ Read server/src/integrity.spec.ts 
→ Read server/src/events/event.service.ts 
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/src/events/event.schema.ts 
→ Read server/src/events/event.controller.ts 
→ Read server/src/dto/create-event.dto.ts 
$ cd /home/maksibon/projects/warhammerMap/server && cat package.json && ls
{
  "name": "server-app",
  "version": "0.0.1",
  "description": "",
  "author": "",
  "private": true,
  "license": "UNLICENSED",
  "scripts": {
    "build": "nest build",
    "format": "prettier --write \"src/**/*.ts\"",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "start:debug": "nest start --debug --watch",
    "start:prod": "node dist/main",
    "lint": "eslint \"src/**/*.ts\" --fix",
    "test": "jest",
    "db:check": "node dist/scripts/db-check",
    "seed": "node dist/scripts/seed",
    "test:watch": "jest --watch",
    "test:cov": "jest --coverage",
    "test:debug": "node --inspect-brk -r tsconfig-paths/register -r ts-node/register node_modules/.bin/jest --runInBand"
  },
  "dependencies": {
    "@nestjs/common": "^11.0.1",
    "@nestjs/config": "^4.0.2",
    "@nestjs/core": "^11.0.1",
    "@nestjs/mapped-types": "^12.0.0",
    "@nestjs/mongoose": "^11.0.3",
    "@nestjs/platform-express": "^11.0.1",
    "class-transformer": "^0.5.1",
    "class-validator": "^0.15.1",
    "mongoose": "^8.15.1",
    "reflect-metadata": "^0.2.2",
    "rxjs": "^7.8.1"
  },
  "devDependencies": {
    "@eslint/eslintrc": "^3.2.0",
    "@eslint/js": "^9.18.0",
    "@nestjs/cli": "^11.0.0",
    "@nestjs/schematics": "^11.0.0",
    "@nestjs/testing": "^11.0.1",
    "@swc/cli": "^0.6.0",
    "@swc/core": "^1.10.7",
    "@types/express": "^5.0.0",
    "@types/jest": "^29.5.14",
    "@types/multer": "^1.4.13",
    "@types/node": "^22.10.7",
    "@types/supertest": "^6.0.2",
    "globals": "^16.0.0",
    "jest": "^29.7.0",
    "source-map-support": "^0.5.21",
    "supertest": "^7.0.0",
    "ts-jest": "^29.2.5",
    "ts-loader": "^9.5.2",
    "ts-node": "^10.9.2",
    "tsconfig-paths": "^4.2.0",
    "typescript": "^5.7.3",
    "typescript-eslint": "^8.20.0"
  },
  "jest": {
    "moduleFileExtensions": [
      "js",
      "json",
      "ts"
    ],
    "rootDir": "src",
    "testRegex": ".*\\.spec\\.ts$",
    "transform": {
      "^.+\\.(t|j)s$": "ts-jest"
    },
    "collectCoverageFrom": [
      "**/*.(t|j)s"
    ],
    "coverageDirectory": "../coverage",
    "testEnvironment": "node",
    "modulePaths": [
      "<rootDir>/.."
    ]
  }
}
dist
Dockerfile
eslint.config.mjs
nest-cli.json
node_modules
package.json
package-lock.json
seed
src
tsconfig.build.json
tsconfig.json
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && ls src && find src -name '*.spec.ts' -o -name '*.e2e-spec.ts' | sort && (mongosh --quiet --eval 'db.runCommand({ping:1})' 2>&1 | head -5 || true) && ls -a | head -20
auth
common
dto
error-holder.ts
events
files
integrity.spec.ts
legions
main-app.module.ts
main.ts
objects.module.ts
planets
scripts
src/auth/admin.guard.spec.ts
src/dto/update-event.dto.spec.ts
src/files/create-cleanup.spec.ts
src/files/file.service.spec.ts
src/integrity.spec.ts
zsh:1: command not found: mongosh
.
..
dist
Dockerfile
.dockerignore
.env.example
eslint.config.mjs
.gitignore
nest-cli.json
node_modules
package.json
package-lock.json
.prettierrc
seed
src
tsconfig.build.json
tsconfig.json
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && npx jest 2>&1 | tail -60
PASS src/auth/admin.guard.spec.ts
PASS src/dto/update-event.dto.spec.ts
PASS src/files/create-cleanup.spec.ts
PASS src/files/file.service.spec.ts
PASS src/integrity.spec.ts (5.383 s)

Test Suites: 5 passed, 5 total
Tests:       38 passed, 38 total
Snapshots:   0 total
Time:        6.273 s
Ran all test suites.
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && npx tsc --noEmit 2>&1 | tail -30; echo "exit=$?"
exit=0
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/tsconfig.json 
→ Read server/src/error-holder.ts 
→ Read server/src/common/parse-object-id.pipe.ts 
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && grep -rn "mapped-types\|PartialType" src | head -20
src/integrity.spec.ts:10:jest.mock('@nestjs/mapped-types', () => ({ PartialType: (type: unknown) => type }));
src/dto/create-planet.dto.ts:1:import { PartialType } from '@nestjs/mapped-types';
src/dto/create-planet.dto.ts:41:export class UpdatePlanetDto extends PartialType(CreatePlanetDto) {}
src/dto/create-legion.dto.ts:1:import { PartialType } from '@nestjs/mapped-types';
src/dto/create-legion.dto.ts:14:export class UpdateLegionDto extends PartialType(CreateLegionDto) {}
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && npx ts-node -e '
require("reflect-metadata");
const { Test } = require("@nestjs/testing");
const { MongooseModule } = require("@nestjs/mongoose");
const { ValidationPipe } = require("@nestjs/common");
const request = require("supertest");
const { ObjectModule } = require("src/objects.module");
const PNG = Buffer.from("png-bytes");
(async () => {
  const module = await Test.createTestingModule({ imports: [MongooseModule.forRoot("mongodb://localhost:27017/warhammer_a_test"), ObjectModule] }).compile();
  const app = module.createNestApplication();
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  await app.init();
  const http = () => request(app.getHttpServer());
  await http().delete("/events"); await http().delete("/planets"); await http().delete("/legions");
  const planet = (await http().post("/planets").field("name","P").field("size",50).field("top",10).field("left",20).attach("pic", PNG, {filename:"p.png",contentType:"image/png"}).expect(201)).body;
  const event = (await http().post("/events").field("name","E").field("description","D").field("link","L").field("place", planet._id).attach("shots", PNG, {filename:"s.png",contentType:"image/png"}).expect(201)).body;
  console.log("created", JSON.stringify({shots: event.shots, name: event.name, desc: event.description, link: event.link}));
  const cases = [{name:""},{name:null},{place:null},{place:"not-an-id"},{shots:["hack.png"]},{description:null},{link:5},{unknownField:1}];
  for (const body of cases) {
    const res = await http().put("/events/" + event._id).send(body);
    console.log("PUT", JSON.stringify(body), "->", res.status, JSON.stringify(res.body).slice(0,180));
  }
  const after = (await http().get("/events/" + event._id)).body;
  console.log("after invalid attempts:", JSON.stringify({shots: after.shots, name: after.name, desc: after.description, link: after.link, place: after.place}));
  // valid partial with shots sent
  const ok = await http().put("/events/" + event._id).send({ name: "E2", shots: ["hacked.png"] });
  console.log("PUT name+shots ->", ok.status, JSON.stringify({name: ok.body.name, shots: ok.body.shots, desc: ok.body.description, link: ok.body.link, place: ok.body.place}));
  // move to same planet, then unknown
  const same = await http().put("/events/" + event._id).send({ place: planet._id });
  console.log("PUT same place ->", same.status);
  const missing = "0123456789abcdef01234567";
  const r1 = await http().put("/events/" + missing).send({ name: "Ghost" });
  console.log("PUT unknown event ->", r1.status, JSON.stringify(r1.body).slice(0,150));
  const r2 = await http().put("/events/" + event._id).send({ place: missing });
  console.log("PUT unknown planet ->", r2.status, JSON.stringify(r2.body).slice(0,150));
  const final = (await http().get("/events/" + event._id)).body;
  console.log("final:", JSON.stringify({name: final.name, place: final.place, shots: final.shots}));
  const bug = await http().put("/events/" + event._id).send({ place: "not-an-id" });
  console.log("PUT bad place format ->", bug.status);
  const badId = await http().put("/events/not-an-id").send({ name: "x" });
  console.log("PUT malformed event id ->", badId.status);
  await app.close();
  process.exit(0);
})().catch((e) => { console.error("FAILED", e); process.exit(1); });
' 2>&1 | tail -40
node:internal/modules/cjs/loader:1568
  throw err;
  ^

Error: Cannot find module 'src/objects.module'
Require stack:
- /home/maksibon/projects/warhammerMap/server/[eval].ts
    at Module.<anonymous> (node:internal/modules/cjs/loader:1564:15)
    at Module._resolveFilename.sharedData.moduleResolveFilenameHook.installedValue [as _resolveFilename] (/home/maksibon/projects/warhammerMap/server/node_modules/@cspotcode/source-map-support/source-map-support.js:811:30)
    at wrapResolveFilename (node:internal/modules/cjs/loader:1118:27)
    at defaultResolveImplForCJSLoading (node:internal/modules/cjs/loader:1142:10)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1169:12)
    at Module._load (node:internal/modules/cjs/loader:1341:5)
    at wrapModuleLoad (node:internal/modules/cjs/loader:261:19)
    at Module.require (node:internal/modules/cjs/loader:1674:12)
    at /home/maksibon/projects/warhammerMap/server/[eval].ts:7:26
    at Script.runInThisContext (node:vm:137:12) {
  code: 'MODULE_NOT_FOUND',
  requireStack: [ '/home/maksibon/projects/warhammerMap/server/[eval].ts' ]
}
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && npx ts-node -r tsconfig-paths/register -e '
require("reflect-metadata");
const { Test } = require("@nestjs/testing");
const { MongooseModule } = require("@nestjs/mongoose");
const { ValidationPipe } = require("@nestjs/common");
const request = require("supertest");
const { ObjectModule } = require("./src/objects.module");
const PNG = Buffer.from("png-bytes");
(async () => {
  const module = await Test.createTestingModule({ imports: [MongooseModule.forRoot("mongodb://localhost:27017/warhammer_a_test"), ObjectModule] }).compile();
  const app = module.createNestApplication();
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  await app.init();
  const http = () => request(app.getHttpServer());
  await http().delete("/events"); await http().delete("/planets"); await http().delete("/legions");
  const planet = (await http().post("/planets").field("name","P").field("size",50).field("top",10).field("left",20).attach("pic", PNG, {filename:"p.png",contentType:"image/png"}).expect(201)).body;
  const event = (await http().post("/events").field("name","E").field("description","D").field("link","L").field("place", planet._id).attach("shots", PNG, {filename:"s.png",contentType:"image/png"}).expect(201)).body;
  console.log("created", JSON.stringify({shots: event.shots, name: event.name, desc: event.description, link: event.link}));
  const cases = [{name:""},{name:null},{place:null},{place:"not-an-id"},{shots:["hack.png"]},{description:null},{link:5},{unknownField:1}];
  for (const body of cases) {
    const res = await http().put("/events/" + event._id).send(body);
    console.log("PUT", JSON.stringify(body), "->", res.status, JSON.stringify(res.body).slice(0,180));
  }
  const after = (await http().get("/events/" + event._id)).body;
  console.log("after invalid attempts:", JSON.stringify({shots: after.shots, name: after.name, desc: after.description, link: after.link, place: after.place}));
  const ok = await http().put("/events/" + event._id).send({ name: "E2", shots: ["hacked.png"] });
  console.log("PUT name+shots ->", ok.status, JSON.stringify({name: ok.body.name, shots: ok.body.shots, desc: ok.body.description, link: ok.body.link, place: ok.body.place}));
  const same = await http().put("/events/" + event._id).send({ place: planet._id });
  console.log("PUT same place ->", same.status);
  const missing = "0123456789abcdef01234567";
  const r1 = await http().put("/events/" + missing).send({ name: "Ghost" });
  console.log("PUT unknown event ->", r1.status, JSON.stringify(r1.body).slice(0,150));
  const r2 = await http().put("/events/" + event._id).send({ place: missing });
  console.log("PUT unknown planet ->", r2.status, JSON.stringify(r2.body).slice(0,150));
  const final = (await http().get("/events/" + event._id)).body;
  console.log("final:", JSON.stringify({name: final.name, place: final.place, shots: final.shots}));
  const bug = await http().put("/events/" + event._id).send({ place: "not-an-id" });
  console.log("PUT bad place format ->", bug.status);
  const badId = await http().put("/events/not-an-id").send({ name: "x" });
  console.log("PUT malformed event id ->", badId.status);
  await app.close();
  process.exit(0);
})().catch((e) => { console.error("FAILED", e); process.exit(1); });
' 2>&1 | tail -40
[Nest] 725874  - 10/29/2026, 2:10:24 AM   ERROR [ExceptionsHandler] Error: Event validation failed: name: Path `name` is required.
    at ValidationError.inspect (/home/maksibon/projects/warhammerMap/server/node_modules/mongoose/lib/error/validation.js:52:26)
    at formatValue (node:internal/util/inspect:895:19)
    at inspect (node:internal/util/inspect:407:10)
    at TestingLogger.stringifyMessage (/home/maksibon/projects/warhammerMap/server/node_modules/@nestjs/common/services/console-logger.service.js:205:47)
    at TestingLogger.formatMessage (/home/maksibon/projects/warhammerMap/server/node_modules/@nestjs/common/services/console-logger.service.js:186:29)
    at /home/maksibon/projects/warhammerMap/server/node_modules/@nestjs/common/services/console-logger.service.js:153:43
    at Array.forEach (<anonymous>)
    at TestingLogger.printMessages (/home/maksibon/projects/warhammerMap/server/node_modules/@nestjs/common/services/console-logger.service.js:139:18)
    at TestingLogger.error (/home/maksibon/projects/warhammerMap/server/node_modules/@nestjs/common/services/console-logger.service.js:65:14)
    at TestingLogger.error (/home/maksibon/projects/warhammerMap/server/node_modules/@nestjs/testing/services/testing-logger.service.js:17:22) {
  errors: {
    name: ValidatorError: Path `name` is required.
        at validate (/home/maksibon/projects/warhammerMap/server/node_modules/mongoose/lib/schemaType.js:1404:13)
        at SchemaString.SchemaType.doValidate (/home/maksibon/projects/warhammerMap/server/node_modules/mongoose/lib/schemaType.js:1388:7)
        at /home/maksibon/projects/warhammerMap/server/node_modules/mongoose/lib/document.js:3096:18
        at processTicksAndRejections (node:internal/process/task_queues:85:11) {
      properties: {
        validator: [Function (anonymous)],
        message: 'Path `name` is required.',
        type: 'required',
        path: 'name',
        fullPath: undefined,
        value: undefined
      },
      kind: 'required',
      path: 'name',
      value: undefined,
      reason: undefined,
      Symbol(mongoose#validatorError): true
    }
  },
  _message: 'Event validation failed'
}
PUT same place -> 500
PUT unknown event -> 404 {"message":"Object with id 0123456789abcdef01234567 not found","error":"Not Found","statusCode":404}
PUT unknown planet -> 404 {"message":"Planet 0123456789abcdef01234567 not found","error":"Not Found","statusCode":404}
final: {"name":"E2","place":"6ae280e0ece83bec0c95c892","shots":["6ae280e0ece83bec0c95c897.png"]}
PUT bad place format -> 400
PUT malformed event id -> 400
> plan · deepseek/deepseek-v4.1-flash-1017
The tests pass, but my manual HTTP check hit a 500. Let me get the full detail before drawing conclusions.
$ cd /home/maksibon/projects/warhammerMap/server && npx ts-node -r tsconfig-paths/register -e '
require("reflect-metadata");
const { ValidationPipe } = require("@nestjs/common");
const { UpdateEventDto } = require("./src/dto/update-event.dto");
(async () => {
  const pipe = new ValidationPipe({ whitelist: true, transform: true });
  for (const body of [{name:"E2"},{place:"6ae280e0ece83bec0c95c892"},{name:"",},{name:null},{place:null},{shots:["x"]},{}]) {
    try {
      const dto = await pipe.transform(body, {type:"body", metatype: UpdateEventDto});
      console.log(JSON.stringify(body), "=> own keys:", Object.keys(dto), "JSON:", JSON.stringify(dto), "assign to doc:", JSON.stringify(Object.assign({name:"KEEP", description:"KEEP", link:"KEEP", shots:["KEEP"], place:"KEEP"}, dto)));
    } catch (e) { console.log(JSON.stringify(body), "=> REJECT", e.constructor.name, JSON.stringify(e.getResponse ? e.getResponse() : e.message)); }
  }
})();
' 2>&1 | tail -20
{"name":"E2"} => own keys: [ 'name', 'description', 'link', 'place' ] JSON: {"name":"E2"} assign to doc: {"name":"E2","shots":["KEEP"]}
{"place":"6ae280e0ece83bec0c95c892"} => own keys: [ 'name', 'description', 'link', 'place' ] JSON: {"place":"6ae280e0ece83bec0c95c892"} assign to doc: {"shots":["KEEP"],"place":"6ae280e0ece83bec0c95c892"}
{"name":""} => REJECT BadRequestException {"message":["name should not be empty"],"error":"Bad Request","statusCode":400}
{"name":null} => REJECT BadRequestException {"message":["name should not be empty","name must be a string"],"error":"Bad Request","statusCode":400}
{"place":null} => REJECT BadRequestException {"message":["place must be a mongodb id"],"error":"Bad Request","statusCode":400}
{"shots":["x"]} => own keys: [ 'name', 'description', 'link', 'place' ] JSON: {} assign to doc: {"shots":["KEEP"]}
{} => own keys: [ 'name', 'description', 'link', 'place' ] JSON: {} assign to doc: {"shots":["KEEP"]}
> plan · deepseek/deepseek-v4.1-flash-1017
The 500 is reproducible. Now let me run the full scenario set under the same ValidationPipe that `main.ts` installs (the jest integration app does not install it).
$ cd /home/maksibon/projects/warhammerMap/server && npx ts-node -r tsconfig-paths/register -e '
require("reflect-metadata");
const { Test } = require("@nestjs/testing");
const { MongooseModule, getConnectionToken } = require("@nestjs/mongoose");
const { ValidationPipe } = require("@nestjs/common");
const request = require("supertest");
const { ObjectModule } = require("./src/objects.module");
const { checkIntegrity } = require("./src/scripts/db-check");
const PNG = Buffer.from("png-bytes");
(async () => {
  const module = await Test.createTestingModule({ imports: [MongooseModule.forRoot("mongodb://localhost:27017/warhammer_a_test"), ObjectModule] }).compile();
  const app = module.createNestApplication();
  app.useLogger(false);
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  await app.init();
  const http = () => request(app.getHttpServer());
  const conn = module.get(getConnectionToken());
  const reset = async () => { await http().delete("/events"); await http().delete("/planets"); await http().delete("/legions"); };
  const planet = async (n) => (await http().post("/planets").field("name",n).field("size",50).field("top",10).field("left",20).attach("pic", PNG, {filename:"p.png",contentType:"image/png"}).expect(201)).body;
  const event = async (p, name="Hunt", extra={}) => { let r = http().post("/events").field("name",name).field("description","Old").field("link","https://example.invalid/hunt").field("place",p); r = r.attach("shots", PNG, {filename:"s.png",contentType:"image/png"}); return (await r.expect(201)).body; };
  const issues = async () => Object.values(await checkIntegrity(conn)).flat();
  const show = (e) => ({name:e.name, description:e.description, link:e.link, place:e.place, shots:e.shots});

  await reset();
  let p1 = await planet("Fenris"); let p2 = await planet("Second");
  let e = await event(p1._id);
  console.log("[setup] event:", JSON.stringify(show(e)));

  console.log("\n--- MAIN 1: partial PUT {name} ---");
  let r = await http().put("/events/"+e._id).send({name:"Great Hunt"});
  console.log("status:", r.status, "body:", JSON.stringify(r.body));
  let g = (await http().get("/events/"+e._id).body ? null : null);
  g = (await http().get("/events/"+e._id)).body;
  console.log("GET after:", JSON.stringify(show(g)));

  console.log("\n--- MAIN 2: PUT {description, place} move only ---");
  await reset(); p1 = await planet("First"); p2 = await planet("Second");
  e = await event(p1._id);
  r = await http().put("/events/"+e._id).send({description:"Updated", place:p2._id});
  console.log("status:", r.status, "body:", JSON.stringify(r.body));
  console.log("p1.events:", JSON.stringify((await http().get("/planets/"+p1._id)).body.events.map(x=>x._id)), "p2.events:", JSON.stringify((await http().get("/planets/"+p2._id)).body.events.map(x=>x._id)));

  console.log("\n--- MAIN 2b: PUT {name, place} move with name ---");
  await reset(); p1 = await planet("First"); p2 = await planet("Second");
  e = await event(p1._id);
  r = await http().put("/events/"+e._id).send({name:"Landing", place:p2._id});
  console.log("status:", r.status, "body:", JSON.stringify(r.body && show(r.body)));
  console.log("p1.events:", JSON.stringify((await http().get("/planets/"+p1._id)).body.events.map(x=>x._id)), "p2.events:", JSON.stringify((await http().get("/planets/"+p2._id)).body.events.map(x=>x._id)));
  console.log("integrity issues:", JSON.stringify(await issues()));

  console.log("\n--- MAIN 3: shots in body ---");
  await reset(); p1 = await planet("Terra"); e = await event(p1._id);
  const beforeShots = e.shots.slice();
  r = await http().put("/events/"+e._id).send({name:"N", shots:["hacked.png"]});
  console.log("status:", r.status, "shots equal:", JSON.stringify(r.body.shots) === JSON.stringify(beforeShots), JSON.stringify(r.body.shots));

  console.log("\n--- ERROR: invalid values ---");
  await reset(); p1 = await planet("Terra"); e = await event(p1._id);
  for (const body of [{name:""},{name:null},{place:null},{place:"not-an-id"},{name:5}]) {
    r = await http().put("/events/"+e._id).send(body);
    console.log(JSON.stringify(body), "->", r.status);
  }
  g = (await http().get("/events/"+e._id)).body;
  console.log("event after invalid:", JSON.stringify(show(g)));

  console.log("\n--- ERROR: unknown event/planet ---");
  const missing = "0123456789abcdef01234567";
  r = await http().put("/events/"+missing).send({name:"Ghost"}); console.log("unknown event ->", r.status);
  r = await http().put("/events/"+e._id).send({place:missing}); console.log("unknown planet ->", r.status);
  g = (await http().get("/events/"+e._id)).body; console.log("event after:", JSON.stringify(show(g)));

  await app.close(); process.exit(0);
})().catch((e) => { console.error("FAILED", e); process.exit(1); });
' 2>&1
[setup] event: {"name":"Hunt","description":"Old","link":"https://example.invalid/hunt","place":"6ae281027c16e6c6b7cf4504","shots":["6ae281027c16e6c6b7cf450f.png"]}

--- MAIN 1: partial PUT {name} ---
status: 200 body: {"_id":"6ae281027c16e6c6b7cf4511","name":"Great Hunt","shots":["6ae281027c16e6c6b7cf450f.png"],"place":"6ae281027c16e6c6b7cf4504","createdAt":"2026-10-28T23:10:58.687Z","updatedAt":"2026-10-28T23:10:58.708Z","__v":0}
GET after: {"name":"Great Hunt","place":"6ae281027c16e6c6b7cf4504","shots":["6ae281027c16e6c6b7cf450f.png"]}

--- MAIN 2: PUT {description, place} move only ---
status: 500 body: {"statusCode":500,"message":"Internal server error"}
p1.events: ["6ae281027c16e6c6b7cf4534"] p2.events: []

--- MAIN 2b: PUT {name, place} move with name ---
status: 200 body: {"name":"Landing","place":"6ae281027c16e6c6b7cf454f","shots":["6ae281027c16e6c6b7cf4554.png"]}
p1.events: [] p2.events: ["6ae281027c16e6c6b7cf4556"]
integrity issues: []

--- MAIN 3: shots in body ---
status: 200 shots equal: true ["6ae281037c16e6c6b7cf4573.png"]

--- ERROR: invalid values ---
{"name":""} -> 400
{"name":null} -> 400
{"place":null} -> 400
{"place":"not-an-id"} -> 400
{"name":5} -> 400
event after invalid: {"name":"Hunt","description":"Old","link":"https://example.invalid/hunt","place":"6ae281037c16e6c6b7cf458a","shots":["6ae281037c16e6c6b7cf458f.png"]}

--- ERROR: unknown event/planet ---
unknown event -> 404
unknown planet -> 404
event after: {"name":"Hunt","description":"Old","link":"https://example.invalid/hunt","place":"6ae281037c16e6c6b7cf458a","shots":["6ae281037c16e6c6b7cf458f.png"]}
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap && find openspec/changes/add-event-edit -type f | sort && ls specs 2>/dev/null | head
openspec/changes/add-event-edit/design.md
openspec/changes/add-event-edit/evidence/review.md
openspec/changes/add-event-edit/evidence/verify.md
openspec/changes/add-event-edit/.openspec.yaml
openspec/changes/add-event-edit/proposal.md
openspec/changes/add-event-edit/specs/events/spec.md
openspec/changes/add-event-edit/tasks.md
user-story-3.md
$ cd /home/maksibon/projects/warhammerMap/server && npx ts-node -r tsconfig-paths/register -e '
const { UpdateEventDto } = require("./src/dto/update-event.dto");
const inst = new UpdateEventDto();
console.log("fresh instance own keys:", Object.keys(inst), "name in instance:", "name" in inst);
' 2>&1 | tail -3 && grep -rn "useGlobalPipes\|ValidationPipe" src --include=*.ts | grep -v node_modules
fresh instance own keys: [ 'name', 'description', 'link', 'place' ] name in instance: true
zsh:5: no matches found: --include=*.ts
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read openspec/changes/add-event-edit/tasks.md 
→ Read openspec/changes/add-event-edit/evidence/verify.md 
$ cd /home/maksibon/projects/warhammerMap/server && grep -rn "ValidationPipe\|useGlobalPipes" src | grep -v node_modules
src/dto/update-event.dto.spec.ts:1:import { BadRequestException, ValidationPipe } from '@nestjs/common';
src/dto/update-event.dto.spec.ts:5:    const pipe = new ValidationPipe({ whitelist: true, transform: true });
src/main.ts:1:import { ValidationPipe } from '@nestjs/common';
src/main.ts:9:    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read openspec/changes/add-event-edit/design.md 
$ cd /home/maksibon/projects/warhammerMap && grep -rn "старый\|старого\|old\|Старый" openspec/changes/add-event-edit/{design.md,proposal.md,evidence/review.md} | head -20
openspec/changes/add-event-edit/evidence/review.md:25:→ Read server/src/error-holder.ts 
openspec/changes/add-event-edit/evidence/review.md:282:                    placeholder="https://"
openspec/changes/add-event-edit/evidence/review.md:800:-rw-r--r--  1 maksibon users    229 окт 15 00:51 error-holder.d.ts
openspec/changes/add-event-edit/evidence/review.md:801:-rw-r--r--  1 maksibon users    934 окт 15 00:51 error-holder.js
openspec/changes/add-event-edit/evidence/review.md:802:-rw-r--r--  1 maksibon users    715 окт 15 00:51 error-holder.js.map
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read specs/user-story-3.md 
$ cd /home/maksibon/projects/warhammerMap && head -80 openspec/changes/add-event-edit/evidence/review.md
> plan · deepseek/deepseek-v4.1-flash-1017
I'll read the OpenSpec proposal files and the related code, then report concrete gaps.
⚙ execute {"code":"const base = \"/home/maksibon/projects/warhammerMap\";\nconst files = [\n  \"openspec/changes/add-event-edit/proposal.md\",\n  \"openspec/changes/add-event-edit/specs/events/spec.md\",\n  \"openspec/changes/add-event-edit/design.md\",\n  \"openspec/changes/add-event-edit/tasks.md\",\n];\nconst results = await Promise.allSettled(files.map(f => tools.read({path: `${base}/${f}`})));\nresults.forEach((r, i) => {\n  if (r.status === \"rejected\") console.log(`READ FAILED ${files[i]}: ${r.reason}`);\n  else console.log(`\\n===== ${files[i]} =====\\n${r.value.content}`);\n});"} 
✱ Glob "server/src/{events,dto}/**/*" 7 matches
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read openspec/changes/add-event-edit/proposal.md 
→ Read openspec/changes/add-event-edit/design.md 
→ Read openspec/changes/add-event-edit/tasks.md 
→ Read openspec/changes/add-event-edit/specs/events/spec.md 
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/src/events/event.schema.ts 
→ Read server/src/events/event.controller.ts 
→ Read server/src/events/event.service.ts 
→ Read server/src/main.ts 
→ Read server/src/integrity.spec.ts 
→ Read server/src/dto/create-event.dto.ts 
→ Read server/src/dto/update-event.dto.ts 
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/src/common/parse-object-id.pipe.ts 
→ Read server/src/planets/planets.service.ts 
→ Read server/src/planets/planets.schema.ts 
→ Read README.md 
→ Read server/package.json 
→ Read server/src/error-holder.ts 
→ Read server/src/scripts/db-check.ts 
> plan · deepseek/deepseek-v4.1-flash-1017
✱ Grep "events/|updateEvent|editEvent|PUT|put\(" in client · 5 matches
$ ls -la openspec openspec/specs openspec/changes 2>/dev/null; echo '---'; cat openspec/project.md 2>/dev/null | head -80; echo '--- mapped-types version'; cat server/node_modules/@nestjs/mapped-types/package.json 2>/dev/null | grep '"version"'; grep -n 'mapped-types' server/package-lock.json | head
openspec:
total 20
drwxr-xr-x  4 maksibon users 4096 окт 29 02:00 .
drwxr-xr-x 10 maksibon users 4096 окт 29 02:00 ..
drwxr-xr-x  4 maksibon users 4096 окт 29 02:01 changes
-rw-r--r--  1 maksibon users  768 окт 29 02:00 config.yaml
drwxr-xr-x  2 maksibon users 4096 окт 29 02:00 specs

openspec/changes:
total 16
drwxr-xr-x 4 maksibon users 4096 окт 29 02:01 .
drwxr-xr-x 4 maksibon users 4096 окт 29 02:00 ..
drwxr-xr-x 4 maksibon users 4096 окт 29 02:02 add-event-edit
drwxr-xr-x 2 maksibon users 4096 окт 29 02:00 archive

openspec/specs:
total 8
drwxr-xr-x 2 maksibon users 4096 окт 29 02:00 .
drwxr-xr-x 4 maksibon users 4096 окт 29 02:00 ..
-rw-r--r-- 1 maksibon users    0 окт 29 02:00 .gitkeep
---
--- mapped-types version
  "version": "12.0.0",
15:        "@nestjs/mapped-types": "^12.0.0",
2546:    "node_modules/@nestjs/mapped-types": {
2548:      "resolved": "https://registry.npmjs.org/@nestjs/mapped-types/-/mapped-types-12.0.0.tgz",
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read openspec/config.yaml 
→ Read server/src/objects.module.ts 
→ Read server/src/main-app.module.ts 
→ Read client/lib/slices/planetSlices.ts 
$ find openspec/changes/add-event-edit -type f -maxdepth 4 | sort; echo '---'; ls -la openspec/changes/archive; echo '--- guard'; sed -n '1,120p' server/src/auth/admin.guard.ts 2>/dev/null
openspec/changes/add-event-edit/design.md
openspec/changes/add-event-edit/evidence/review.md
openspec/changes/add-event-edit/.openspec.yaml
openspec/changes/add-event-edit/proposal.md
openspec/changes/add-event-edit/specs/events/spec.md
openspec/changes/add-event-edit/tasks.md
---
total 8
drwxr-xr-x 2 maksibon users 4096 окт 29 02:00 .
drwxr-xr-x 4 maksibon users 4096 окт 29 02:01 ..
-rw-r--r-- 1 maksibon users    0 окт 29 02:00 .gitkeep
--- guard
import { CanActivate, ExecutionContext, ForbiddenException, Injectable, UnauthorizedException } from '@nestjs/common';
import { Request } from 'express';

const READ_METHODS = ['GET', 'HEAD', 'OPTIONS'];

interface Session {
    user?: { role?: string };
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd /home/maksibon/projects/warhammerMap/server && cat tsconfig.build.json && sed -n '1,80p' src/scripts/db-check.ts
{
  "extends": "./tsconfig.json",
  "exclude": ["node_modules" ,"test", "dist", "**/*spec.ts"],
  "include": ["src/**/*"]
}
import { Connection, createConnection } from 'mongoose';
import { IMAGES_BUCKET } from '../files/file.service';

interface Doc {
    _id: { toString(): string };
    [field: string]: any;
}

const ids = (values: unknown): string[] => (Array.isArray(values) ? values.map(String) : []);

export async function checkIntegrity(connection: Connection): Promise<Record<string, string[]>> {
    const db = connection.db!;
    const load = (name: string) => db.collection<Doc>(name).find().toArray();
    const [planets, legions, events, files] = await Promise.all([
        load('planets'),
        load('legions'),
        load('events'),
        load(`${IMAGES_BUCKET}.files`),
    ]);
    const planetById = new Map(planets.map((planet) => [String(planet._id), planet]));
    const legionById = new Map(legions.map((legion) => [String(legion._id), legion]));
    const eventById = new Map(events.map((event) => [String(event._id), event]));
    const issues: Record<string, string[]> = {
        'planet -> missing legion': [],
        'legion -> missing planet': [],
        'planet lists legion, legion does not list planet': [],
        'legion lists planet, planet does not list legion': [],
        'planet -> missing event': [],
        'planet lists event, event.place is another planet': [],
        'event.place is not a single planet id': [],
        'event -> missing planet': [],
        'event.place planet does not list the event': [],
        'image referenced but missing in GridFS': [],
        'GridFS file referenced by nothing': [],
    };

    for (const planet of planets) {
        const planetId = String(planet._id);
        for (const legionId of ids(planet.legions)) {
            const legion = legionById.get(legionId);
            if (!legion) issues['planet -> missing legion'].push(`${planetId} -> ${legionId}`);
            else if (!ids(legion.planets).includes(planetId)) {
                issues['planet lists legion, legion does not list planet'].push(`${planetId} / ${legionId}`);
            }
        }
        for (const eventId of ids(planet.events)) {
            const event = eventById.get(eventId);
            if (!event) issues['planet -> missing event'].push(`${planetId} -> ${eventId}`);
            else if (String(event.place) !== planetId) {
                issues['planet lists event, event.place is another planet'].push(`${planetId} / ${eventId}`);
            }
        }
    }
    for (const legion of legions) {
        const legionId = String(legion._id);
        for (const planetId of ids(legion.planets)) {
            const planet = planetById.get(planetId);
            if (!planet) issues['legion -> missing planet'].push(`${legionId} -> ${planetId}`);
            else if (!ids(planet.legions).includes(legionId)) {
                issues['legion lists planet, planet does not list legion'].push(`${legionId} / ${planetId}`);
            }
        }
    }
    for (const event of events) {
        const eventId = String(event._id);
        if (Array.isArray(event.place) || !event.place) {
            issues['event.place is not a single planet id'].push(eventId);
            continue;
        }
        const planet = planetById.get(String(event.place));
        if (!planet) issues['event -> missing planet'].push(`${eventId} -> ${event.place}`);
        else if (!ids(planet.events).includes(eventId)) {
            issues['event.place planet does not list the event'].push(`${eventId} / ${event.place}`);
        }
    }

    const referenced = new Set<string>([
        ...planets.map((planet) => planet.pic),
        ...legions.map((legion) => legion.icon),
        ...events.flatMap((event) => ids(event.shots)),
$ cd /home/maksibon/projects/warhammerMap/server && npx jest src/integrity.spec.ts src/dto/update-event.dto.spec.ts --verbose 2>&1 | tail -40
PASS src/dto/update-event.dto.spec.ts
  UpdateEventDto
    ✓ accepts a partial body and strips shots (8 ms)
    ✓ rejects {"name":""} with 400 (1 ms)
    ✓ rejects {"name":null} with 400 (1 ms)
    ✓ rejects {"place":null} with 400 (1 ms)
    ✓ rejects {"place":"not-an-id"} with 400
    ✓ rejects {"link":5} with 400 (1 ms)

PASS src/integrity.spec.ts
  relations and images stay consistent
    ✓ legion delete clears planets even when legion.planets is out of sync (222 ms)
    ✓ planet delete clears legions even when planet.legions is out of sync (118 ms)
    ✓ the same legion as legion1 and legion2 is stored once (123 ms)
    ✓ update treats legion1 and legion2 as independent slots (217 ms)
    ✓ rejects an unknown legion without touching the planet (73 ms)
    ✓ failed update removes the freshly uploaded pic (96 ms)
    ✓ create, update and list return the same planet shape (88 ms)
    ✓ partial event update keeps the fields that were not sent (91 ms)
    ✓ updates an event and moves its planet relation (123 ms)
    ✓ answers 404 when updating an unknown event or moving it to an unknown planet (101 ms)
    ✓ full lifecycle leaves no dangling refs or orphan files (113 ms)
    ✓ bulk deletes empty the collections and files (74 ms)

Test Suites: 2 passed, 2 total
Tests:       18 passed, 18 total
Snapshots:   0 total
Time:        5.111 s, estimated 6 s
Ran all test suites matching /src\/integrity.spec.ts|src\/dto\/update-event.dto.spec.ts/i.
> plan · deepseek/deepseek-v4.1-flash-1017
Now the legacy/regression scenario under the same production pipe.
$ cd /home/maksibon/projects/warhammerMap/server && npx ts-node -r tsconfig-paths/register -e '
require("reflect-metadata");
const { Test } = require("@nestjs/testing");
const { MongooseModule, getConnectionToken } = require("@nestjs/mongoose");
const { ValidationPipe } = require("@nestjs/common");
const request = require("supertest");
const { ObjectModule } = require("./src/objects.module");
const { checkIntegrity } = require("./src/scripts/db-check");
const PNG = Buffer.from("png-bytes");
(async () => {
  const module = await Test.createTestingModule({ imports: [MongooseModule.forRoot("mongodb://localhost:27017/warhammer_a_test"), ObjectModule] }).compile();
  const app = module.createNestApplication(); app.useLogger(false);
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  await app.init();
  const http = () => request(app.getHttpServer());
  const conn = module.get(getConnectionToken());
  const countFiles = () => conn.db.collection("images.files").countDocuments();
  const issues = async () => Object.values(await checkIntegrity(conn)).flat();
  await http().delete("/events"); await http().delete("/planets"); await http().delete("/legions");
  const p = (await http().post("/planets").field("name","Legacy").field("size",50).field("top",10).field("left",20).attach("pic", PNG, {filename:"p.png",contentType:"image/png"}).expect(201)).body;
  const e = await http().post("/events").field("name","Old").field("description","D").field("link","L").field("place",p._id).attach("shots", PNG, {filename:"s.png",contentType:"image/png"}).expect(201);
  console.log("POST /events ->", e.status, JSON.stringify({name:e.body.name, shots:e.body.shots}));
  console.log("GET /events ->", (await http().get("/events")).status, "count:", (await http().get("/events")).body.length);
  console.log("GET /events/:id ->", (await http().get("/events/"+e.body._id)).status);
  console.log("planet lists event ->", (await http().get("/planets/"+p._id)).body.events.length === 1);
  console.log("files before delete:", await countFiles(), "issues:", JSON.stringify(await issues()));
  console.log("DELETE /events/:id ->", (await http().delete("/events/"+e.body._id)).status, "files after:", await countFiles(), "planet.events:", (await http().get("/planets/"+p._id)).body.events.length);
  const e2 = (await http().post("/events").field("name","Old2").field("place",p._id).expect(201)).body;
  console.log("DELETE /events ->", (await http().delete("/events")).status, "list:", (await http().get("/events")).body.length, "files:", await countFiles());
  console.log("final issues:", JSON.stringify(await issues()));
  await app.close(); process.exit(0);
})().catch((e) => { console.error("FAILED", e); process.exit(1); });
' 2>&1
POST /events -> 201 {"name":"Old","shots":["6ae281301f2a660331895d47.png"]}
GET /events -> 200 count: 1
GET /events/:id -> 200
planet lists event -> true
files before delete: 2 issues: []
DELETE /events/:id -> 200 files after: 1 planet.events: 0
DELETE /events -> 200 list: 0 files: 1
final issues: []
> plan · deepseek/deepseek-v4.1-flash-1017
## Что запускал

MongoDB на `localhost:27017` доступна (тесты подключились к `warhammer_a_test`).

```
$ cd server && npx jest
Test Suites: 5 passed, 5 total
Tests:       38 passed, 38 total
Time:        6.273 s

$ cd server && npx tsc --noEmit
(пусто) exit=0
```

Оба зелёные — но это **не** подтверждает спеку: интеграционные тесты поднимают приложение **без** глобального `ValidationPipe` (`integrity.spec.ts:36-42`), а в `main.ts:9` он есть. Я воспроизвёл production-конфигурацию тем же `ValidationPipe({ whitelist: true, transform: true })` и прогнал HTTP-сценарии.

### Причина, почему тесты не ловят дефект

`UpdateEventDto` при `target: ES2023` создаёт собственные поля класса со значением `undefined`:

```
$ npx ts-node -e 'console.log(Object.keys(new UpdateEventDto()))'
fresh instance own keys: [ 'name', 'description', 'link', 'place' ]

$ pipe.transform({name:"E2"}, ...) -> own keys: [ 'name', 'description', 'link', 'place' ]
assign to doc: {"name":"E2","shots":["KEEP"]}   // description/link/place затёрты undefined
```

`Object.assign(event!, dto)` в `event.service.ts:63` копирует эти `undefined` поверх полей документа. В jest-DTO-тесте это маскируется `toEqual` (игнорирует `undefined`), а в интеграционных тестах DTO вообще не трансформируется — туда приходит обычный объект `{name: ...}`. Поэтому `npx jest` зелёный, а в реальном приложении — нет.

---

## Основной сценарий

### 1. Частичное изменение (`PUT` только с `name`)
**Ожидание:** 200; `description`, `link`, `place` прежние; `GET` возвращает то же.
**Факт:** 200, но `description` и `link` **безвозвратно стёрты** (и в ответе, и в БД).
**Доказательство** (production pipe, событие `description:"Old"`, `link:"https://example.invalid/hunt"`):

```
status: 200
body: {"name":"Great Hunt","shots":[...],"place":"6ae28102...4504",...}
GET after: {"name":"Great Hunt","place":"6ae28102...4504","shots":[...]}
```

`description` и `link` исчезли из `GET`. Требование «Поля, которых нет в запросе, MUST сохраняться» **нарушено** — это потеря данных.
Jest-тест `partial event update keeps the fields that were not sent` проходит только потому, что в нём нет pipe.

### 2. Перенос на другую планету (`PUT` с `place`)
**Ожидание:** 200, событие убрано из старой планеты, добавлено в новую, integrity чистая.
**Факт:** **500**; перенос не выполняется, связи не меняются.
**Доказательство** (`{description:"Updated", place:<second>}`):

```
status: 500 {"statusCode":500,"message":"Internal server error"}
p1.events: ["6ae281027c16e6c6b7cf4534"]   p2.events: []
```

В логе Nest: `Event validation failed: name: Path 'name' is required.` — `name` затёрт в `undefined`, `save()` упал. Это ровно сценарий из спеки («WHEN ... с `place` другой существующей планеты»), и он не работает.

**Вариант с явным `name`** (`{name:"Landing", place:<second>}`) — 200, связи корректны, integrity чистая, но `description`/`link` снова стёрты:

```
status: 200 {"name":"Landing","place":"...454f","shots":[...]}
p1.events: []   p2.events: ["...4556"]
integrity issues: []
```

То есть логика `$pull`/`$addToSet` сама по себе верна, ломает её `Object.assign`.

### 3. Снимки сохраняются
**Ожидание:** `shots` и файлы не меняются, даже если `shots` в теле.
**Факт:** PASS.
**Доказательство:** `{name:"N", shots:["hacked.png"]}` → 200, `shots` прежний; `whitelist` вырезает `shots` из DTO:

```
{"shots":["x"]} => own keys: [ 'name', 'description', 'link', 'place' ]  // shots отсутствует
status: 200 shots equal: true ["6ae281037c16e6c6b7cf4573.png"]
```

---

## Ошибочный сценарий

### 4. Невалидные значения
**Ожидание:** 400, событие не меняется.
**Факт:** PASS.
**Доказательство** (production pipe):

```
{"name":""} -> 400
{"name":null} -> 400
{"place":null} -> 400
{"place":"not-an-id"} -> 400
{"name":5} -> 400
event after invalid: {"name":"Hunt","description":"Old","link":".../hunt","place":"...458a","shots":[...]}
```

### 5. Неизвестное событие / планета
**Ожидание:** 404 (событие при неизвестной планете остаётся на прежней).
**Факт:** PASS.
**Доказательство:**

```
unknown event  -> 404 {"message":"Object with id 0123456789abcdef01234567 not found",...}
unknown planet -> 404 {"message":"Planet 0123456789abcdef01234567 not found",...}
event after: {"name":"Hunt","description":"Old","link":".../hunt","place":"...458a","shots":[...]}
```

Примечание: невалидный по формату id события даёт 400 (`ParseObjectIdPipe`), а не 404 — это не противоречит спеке, т.к. речь о корректном, но отсутствующем id.

---

## Старый (регрессионный) сценарий

**Ожидание:** существующие `POST/GET/DELETE /events`, связи с планетой и файлы не сломаны.
**Факт:** PASS.
**Доказательство** (production pipe):

```
POST /events -> 201 {"name":"Old","shots":["...d47.png"]}
GET /events -> 200 count: 1 ; GET /events/:id -> 200
planet lists event -> true
files before delete: 2 ; issues: []
DELETE /events/:id -> 200 files after: 1 planet.events: 0
DELETE /events -> 200 list: 0 files: 1 (остался pic планеты)
final issues: []
```

Плюс весь прежний набор: `12/12` тестов `integrity.spec.ts` и `38/38` всего — зелёные.

---

## Итог

| Сценарий | Ожидание | Факт |
|---|---|---|
| PUT только `name` | 200, прочие поля целы | 200, `description`/`link` стёрты — **FAIL** |
| PUT с `place` (перенос) | 200, перенос | **500**, переноса нет — **FAIL** |
| Перенос с `name`+`place` | 200, связи целы | 200, связи целы, но неотправленные поля стёрты — **FAIL** по Requirement 1 |
| Снимки | не меняются | PASS |
| Невалидные значения | 400, без изменений | PASS |
| Неизвестное событие/планета | 404 | PASS |
| Старый API | без регрессий | PASS |

**Блокирующие дефекты:**
1. `Object.assign(event!, dto)` в `server/src/events/event.service.ts:63` копирует `undefined`-поля DTO → затирает неотправленные `description`/`link`, а без `name` в теле даёт 500.
2. Как следствие, сценарий переноса из спеки (`PUT` с одним `place`) не работает.

**Пробел в тестах:** интеграционный стенд не включает `ValidationPipe`, поэтому проверяет не тот путь, что `main.ts`; DTO-тест использует `toEqual` и не видит лишние `undefined`-ключи.

**Что нужно поправить (не делал, Plan mode):**
- В сервисе присваивать только определённые ключи (`Object.entries(dto).filter(([,v]) => v !== undefined)`), либо собирать `$set` вручную.
- Добавить интеграционный тест с тем же `ValidationPipe`, что в `main.ts` (и сценарий `PUT` только с `place`).
- В DTO-тесте проверять `Object.keys(dto)`, а не только `toEqual`.

Файлы не менял; команды только читали код и писали тестовые данные в `warhammer_a_test`. Отчёт автора (`tasks.md`/`review.md`) в качестве доказательства не использовал.
