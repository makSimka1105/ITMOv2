
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
}

@Injectable()
export class AdminGuard implements CanActivate {
    async canActivate(context: ExecutionContext): Promise<boolean> {
        const req = context.switchToHttp().getRequest<Request>();
        if (READ_METHODS.includes(req.method)) return true;

        const cookie = req.headers.cookie;
        if (!cookie) throw new UnauthorizedException();

        const session = await this.fetchSession(cookie);
        if (!session?.user) throw new UnauthorizedException();
        if (session.user.role !== 'ADMIN') throw new ForbiddenException();
        return true;
    }

    private async fetchSession(cookie: string): Promise<Session | null> {
        try {
            const res = await fetch(`${process.env.FRONT_URL}/api/auth/get-session`, {
                headers: { cookie },
                signal: AbortSignal.timeout(5000),
            });
            return res.ok ? await res.json() : null;
        } catch {
            return null;
        }
    }
}
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read openspec/changes/add-event-edit/.openspec.yaml 
→ Read openspec/changes/add-event-edit/evidence/review.md 
$ git -C /home/maksibon/projects/warhammerMap status --short; echo '--- log'; git -C /home/maksibon/projects/warhammerMap log --oneline -8; echo '--- diff stat'; git -C /home/maksibon/projects/warhammerMap diff --stat; echo '--- openspec version'; openspec --version 2>/dev/null || npx --no-install openspec --version 2>/dev/null || echo 'no openspec cli'
M README.md
 M server/src/events/event.controller.ts
 M server/src/events/event.service.ts
 M server/src/integrity.spec.ts
?? .opencode/
?? openspec/
?? server/src/dto/update-event.dto.ts
?? specs/
--- log
ab9aeb9 docs: readme with screenshots, architecture and deploy guide
23879e2 chore: single docker compose with seed profile, env examples and render blueprint
2d1249a fix(client): admin create, edit and delete flows, cleanup of dead code
cf21ae3 feat(server): seed script with demo data and db-check for invariants
153ecbd fix(server): keep planet, legion and event relations consistent
96da074 chore: remove course artifacts, agent configs and default readmes
5a83523 docs: practice 4 report, reflection and run evidence
ddc43e8 feat(mcp): image-refs MCP for GridFS orphan and dangling refs
--- diff stat
 README.md                             |  2 +-
 server/src/events/event.controller.ts |  5 +++++
 server/src/events/event.service.ts    | 23 +++++++++++++++++++++++
 server/src/integrity.spec.ts          | 29 +++++++++++++++++++++++++++++
 4 files changed, 58 insertions(+), 1 deletion(-)
--- openspec version
no openspec cli
> plan · deepseek/deepseek-v4.1-flash-1017
✱ Grep "events|PUT|edit|update" in client/components/admin · 0 matches
$ find specs -type f -maxdepth 4 | sort; echo '--- root package'; ls; cat package.json 2>/dev/null | head -40; echo '--- openspec bin'; ls node_modules/.bin 2>/dev/null | head -30; ls server/node_modules/.bin 2>/dev/null | grep -i openspec || echo 'no openspec bin'
specs/user-story-3.md
--- root package
client
docker-compose.dev.yml
docker-compose.yml
docs
openspec
README.md
render.yaml
scripts
server
specs
--- openspec bin
no openspec bin
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read specs/user-story-3.md 
$ ls client/components/admin client/components/search client/app 2>/dev/null; echo '--- refs to createEvent/deleteEvent'; grep -rn "createEvent\|deleteEvent\|updateEvent" client --include=*.tsx --include=*.ts | head -30
client/app:
api
context
icon.png
layout.tsx
login
page.tsx
sign-up
styles
types

client/components/admin:
createObject.tsx
EventCreateDrawer.tsx
legion
planet

client/components/search:
databaseTablet.tsx
itemsColumn.tsx
legionBar.tsx
planetBar.tsx
searchLine.tsx
tabletControls.tsx
tabSwitcher.tsx
--- refs to createEvent/deleteEvent
zsh:1: no matches found: --include=*.tsx
> plan · deepseek/deepseek-v4.1-flash-1017
$ grep -rn "EventCreateDrawer\|createEvent" client --include='*.tsx' --include='*.ts' | head -20; echo '--- drawer'; sed -n '1,80p' client/components/admin/EventCreateDrawer.tsx
client/lib/slices/planetSlices.ts:58:export const createEvent = createAsyncThunk<
client/lib/slices/planetSlices.ts:62:>("events/createEvent", async (newEvent, { rejectWithValue }) => {
client/node_modules/typescript/lib/lib.dom.d.ts:7739:     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Document/createEvent)
client/node_modules/typescript/lib/lib.dom.d.ts:7741:    createEvent(eventInterface: "AnimationEvent"): AnimationEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7742:    createEvent(eventInterface: "AnimationPlaybackEvent"): AnimationPlaybackEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7743:    createEvent(eventInterface: "AudioProcessingEvent"): AudioProcessingEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7744:    createEvent(eventInterface: "BeforeUnloadEvent"): BeforeUnloadEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7745:    createEvent(eventInterface: "BlobEvent"): BlobEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7746:    createEvent(eventInterface: "ClipboardEvent"): ClipboardEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7747:    createEvent(eventInterface: "CloseEvent"): CloseEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7748:    createEvent(eventInterface: "CompositionEvent"): CompositionEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7749:    createEvent(eventInterface: "ContentVisibilityAutoStateChangeEvent"): ContentVisibilityAutoStateChangeEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7750:    createEvent(eventInterface: "CustomEvent"): CustomEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7751:    createEvent(eventInterface: "DeviceMotionEvent"): DeviceMotionEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7752:    createEvent(eventInterface: "DeviceOrientationEvent"): DeviceOrientationEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7753:    createEvent(eventInterface: "DragEvent"): DragEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7754:    createEvent(eventInterface: "ErrorEvent"): ErrorEvent;
client/node_modules/typescript/lib/lib.dom.d.ts:7755:    createEvent(eventInterface: "Event"): Event;
client/node_modules/typescript/lib/lib.dom.d.ts:7756:    createEvent(eventInterface: "Events"): Event;
client/node_modules/typescript/lib/lib.dom.d.ts:7757:    createEvent(eventInterface: "FocusEvent"): FocusEvent;
--- drawer
import React, { useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { IMAGE_ACCEPT, imageError } from "@/lib/imageFile";

const MAX_SHOTS = 4;

interface EventCreateDrawerProps {
    planetId: string | null;
    onClose: () => void;
    onSave: (formData: FormData) => void;
}

interface EventFormProps {
    planetId: string;
    onSave: (formData: FormData) => void;
}

function EventForm({ planetId, onSave }: EventFormProps) {
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [link, setLink] = useState("");
    const [screenshots, setScreenshots] = useState<File[]>([]);

    const handleScreenshotsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setScreenshots(Array.from(e.target.files ?? []));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!title.trim()) {
            toast.error("Укажите название ивента");
            return;
        }
        if (screenshots.length > MAX_SHOTS) {
            toast.error(`Можно прикрепить не больше ${MAX_SHOTS} скриншотов`);
            return;
        }
        const shotError = screenshots.map(imageError).find(Boolean);
        if (shotError) {
            toast.error(shotError);
            return;
        }

        const formData = new FormData();
        formData.append("name", title.trim());
        formData.append("description", description);
        formData.append("link", link);
        formData.append("place", planetId);
        screenshots.forEach((file) => formData.append("shots", file));
        onSave(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="grid gap-4">
            <div className="grid gap-3">
                <Label htmlFor="event-name">Название</Label>
                <Input id="event-name" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>
            <div className="grid gap-3">
                <Label htmlFor="event-description">Описание</Label>
                <Input id="event-description" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="grid gap-3">
                <Label htmlFor="event-link">Ссылка</Label>
                <Input
                    id="event-link"
                    type="url"
                    pattern="https?://.+"
                    placeholder="https://"
                    value={link}
                    onChange={(e) => setLink(e.target.value)}
                />
            </div>
            <div className="grid gap-3">
                <Label htmlFor="event-shots">Скриншоты</Label>
$ ls ~/.opencode 2>/dev/null; find ~/.opencode -maxdepth 4 -iname '*openspec*' 2>/dev/null | head -20; find / -maxdepth 6 -type d -name 'openspec' 2>/dev/null | grep -v projects | head
/home/maksibon/.config/openspec
> plan · deepseek/deepseek-v4.1-flash-1017
$ find /home/maksibon/.config/openspec -maxdepth 4 -type f | head -40; echo '---'; grep -rn "Purpose\|ADDED Requirements\|Spec Delta" /home/maksibon/.config/openspec 2>/dev/null | head -30
/home/maksibon/.config/openspec/config.json
---
$ cd server && npx tsc --noEmit 2>&1 | head -40; echo "exit=$?"
exit=0
> plan · deepseek/deepseek-v4.1-flash-1017
$ cat /home/maksibon/.config/openspec/config.json; echo '--- mongo'; (command -v mongosh || command -v mongo || true); (timeout 2 bash -c '</dev/tcp/127.0.0.1/27017' && echo 'mongo port open') 2>/dev/null || echo 'mongo port closed'
{
  "telemetry": {
    "noticeSeen": true,
    "anonymousId": "abcf51bb-398f-4546-b269-b33b87cd837a"
  }
}
--- mongo
mongo port closed
> plan · deepseek/deepseek-v4.1-flash-1017
$ cat server/node_modules/@nestjs/mapped-types/package.json | head -40; echo '--- dist'; ls server/node_modules/@nestjs/mapped-types/dist | head; echo '--- partial-type'; sed -n '1,80p' server/node_modules/@nestjs/mapped-types/dist/partial-type.helper.js 2>/dev/null
{
  "name": "@nestjs/mapped-types",
  "version": "12.0.0",
  "type": "module",
  "description": "Nest - modern, fast, powerful node.js web framework (@mapped-types)",
  "author": "Kamil Mysliwiec",
  "license": "MIT",
  "url": "https://github.com/nestjs/mapped-types#readme",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "default": "./dist/index.js"
    },
    "./package.json": "./package.json"
  },
  "engines": {
    "node": ">=20.19.0"
  },
  "scripts": {
    "build": "rimraf -rf dist && tsc -p tsconfig.json",
    "lint": "oxlint lib/ --fix",
    "format": "prettier \"{lib,tests}/**/*.ts\" --write",
    "prepublish:npm": "npm run build",
    "publish:npm": "npm publish --access public",
    "prepublish:next": "npm run build",
    "publish:next": "npm publish --access public --tag next",
    "test:e2e": "vitest run",
    "test:e2e:dev": "vitest --watch",
    "test:esm": "npm run build && node tests/esm-smoke.mjs",
    "prerelease": "npm run build",
    "release": "release-it",
    "prepare": "husky"
  },
  "devDependencies": {
    "@commitlint/cli": "21.2.2",
    "@commitlint/config-angular": "21.2.2",
    "@nestjs/common": "12.0.0",
--- dist
index.d.ts
index.js
intersection-type.helper.d.ts
intersection-type.helper.js
mapped-type.interface.d.ts
mapped-type.interface.js
omit-type.helper.d.ts
omit-type.helper.js
partial-type.helper.d.ts
partial-type.helper.js
--- partial-type
import { applyIsOptionalDecorator, applyValidateIfDefinedDecorator, inheritPropertyInitializers, inheritTransformationMetadata, inheritValidationMetadata, } from './type-helpers.utils.js';
export function PartialType(classRef, options = {}) {
    class PartialClassType {
        constructor() {
            inheritPropertyInitializers(this, classRef);
        }
    }
    const propertyKeys = inheritValidationMetadata(classRef, PartialClassType);
    inheritTransformationMetadata(classRef, PartialClassType);
    if (propertyKeys) {
        propertyKeys.forEach((key) => {
            options.skipNullProperties === false
                ? applyValidateIfDefinedDecorator(PartialClassType, key)
                : applyIsOptionalDecorator(PartialClassType, key);
        });
    }
    Object.defineProperty(PartialClassType, 'name', {
        value: `Partial${classRef.name}`,
    });
    return PartialClassType;
}
> plan · deepseek/deepseek-v4.1-flash-1017
$ node --version; cat server/node_modules/@nestjs/mapped-types/package.json | sed -n '/peerDependencies/,/}/p'; echo '--- deps'; cat server/node_modules/@nestjs/mapped-types/package.json | sed -n '/"dependencies"/,/}/p'; echo '--- tsconfig'; cat server/tsconfig.json; echo '--- nest-cli'; cat server/nest-cli.json 2>/dev/null; echo '--- dockerfiles'; find . -maxdepth 3 -iname 'Dockerfile*' -not -path '*/node_modules/*'
v24.21.0
  "peerDependencies": {
    "@nestjs/common": "^10.0.0 || ^11.0.0 || ^12.0.0",
    "class-transformer": "^0.4.0 || ^0.5.0",
    "class-validator": "^0.13.0 || ^0.14.0 || ^0.15.0",
    "reflect-metadata": "^0.1.12 || ^0.2.0"
  },
  "peerDependenciesMeta": {
    "class-validator": {
      "optional": true
    },
--- deps
--- tsconfig
{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2023",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "incremental": true,
    "skipLibCheck": true,
    "strictNullChecks": true,
    "forceConsistentCasingInFileNames": true,
    "noImplicitAny": false,
    "strictBindCallApply": false,
    "noFallthroughCasesInSwitch": false
  }
}
--- nest-cli
{"$schema":"https://json.schemastore.org/nest-cli","collection":"@nestjs/schematics","sourceRoot":"src"}
--- dockerfiles
./server/Dockerfile
./client/Dockerfile
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/Dockerfile 
$ grep -rn "node:" docker-compose.yml docker-compose.dev.yml render.yaml server/Dockerfile 2>/dev/null; echo '--- npm engines'; cat server/package-lock.json | grep -n '"node"' | head -5
server/Dockerfile:1:FROM node:22-alpine AS build
server/Dockerfile:9:FROM node:22-alpine AS runtime
--- npm engines
60:        "node": ">=6.0.0"
78:        "node": "^18.19.1 || ^20.11.1 || >=22.0.0",
139:        "node": "^18.19.1 || ^20.11.1 || >=22.0.0",
162:        "node": "^18.19.1 || ^20.11.1 || >=22.0.0",
186:        "node": ">=18"
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read render.yaml 
$ grep -rn "NODE_VERSION\|node-version\|engine" . --include='*.yml' --include='*.yaml' --include='*.json' --include='Dockerfile*' -l 2>/dev/null | grep -v node_modules | head; echo '--- git show diff'; git -C /home/maksibon/projects/warhammerMap diff server/src/events/event.service.ts server/src/events/event.controller.ts server/src/integrity.spec.ts README.md
./server/package-lock.json
./client/package-lock.json
./render.yaml
--- git show diff
diff --git a/README.md b/README.md
index 26a9c38..6c5f80e 100644
--- a/README.md
+++ b/README.md
@@ -149,7 +149,7 @@ cd client && npx tsc --noEmit && npm run build
 | GET, POST | `/legions` | файл `icon` |
 | GET, PUT, DELETE | `/legions/:id` | удаление убирает легион со всех планет |
 | GET, POST | `/events` | до 4 файлов `shots`, `place` это id планеты |
-| GET, DELETE | `/events/:id` | |
+| GET, PUT, DELETE | `/events/:id` | PUT edits metadata and moves the event between planets |
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
index d45b057..bfbf291 100644
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
@@ -49,6 +50,28 @@ export class EventService {
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
+        const previousPlace = event!.place;
+        Object.assign(event!, dto);
+        event!.place = place._id;
+        await event!.save();
+
+        if (previousPlace.toString() !== place._id.toString()) {
+            await this.planetModel.updateOne({ _id: previousPlace }, { $pull: { events: event!._id } });
+            await this.planetModel.updateOne({ _id: place._id }, { $addToSet: { events: event!._id } });
+        }
+        return event!;
+    }
+
     async deleteOne(id: string): Promise<{ id: string }> {
         const event = await this.eventModel.findByIdAndDelete(id).exec();
         handleObjNotFound(event, id)
diff --git a/server/src/integrity.spec.ts b/server/src/integrity.spec.ts
index de45fff..cc9308c 100644
--- a/server/src/integrity.spec.ts
+++ b/server/src/integrity.spec.ts
@@ -122,6 +122,35 @@ describe('relations and images stay consistent', () => {
         expect(Object.keys(planet).sort()).toEqual(Object.keys(listed).sort());
     });
 
+    it('updates an event and moves its planet relation', async () => {
+        const first = await createPlanet('First');
+        const second = await createPlanet('Second');
+        const event = (await http().post('/events').field('name', 'Landing').field('place', first._id)
+            .attach('shots', PNG, { filename: 's.png', contentType: 'image/png' }).expect(201)).body;
+
+        const updated = (await http().put(`/events/${event._id}`).send({
+            name: 'Battle',
+            description: 'Updated',
+            place: second._id,
+        }).expect(200)).body;
+
+        expect(updated).toMatchObject({ name: 'Battle', description: 'Updated', place: second._id });
+        expect(updated.shots).toEqual(event.shots);
+        expect((await http().get(`/planets/${first._id}`)).body.events).toEqual([]);
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
→ Read server/src/dto/create-planet.dto.ts 
$ git -C /home/maksibon/projects/warhammerMap show HEAD:server/src/integrity.spec.ts | sed -n '1,15p'; echo '--- jest mock history'; git -C /home/maksibon/projects/warhammerMap log -S "jest.mock('@nestjs/mapped-types'" --oneline -- server/src/integrity.spec.ts
import { INestApplication } from '@nestjs/common';
import { getConnectionToken, MongooseModule } from '@nestjs/mongoose';
import { Test } from '@nestjs/testing';
import { Connection } from 'mongoose';
import * as request from 'supertest';
import { PlanetService } from 'src/planets/planets.service';
import { ObjectModule } from 'src/objects.module';
import { checkIntegrity } from 'src/scripts/db-check';

jest.mock('@nestjs/mapped-types', () => ({ PartialType: (type: unknown) => type }));

const MONGO_URL = `${process.env.MONGO_TEST_URL ?? 'mongodb://localhost:27017'}/warhammer_a_test`;
const PNG = Buffer.from('png-bytes');

describe('relations and images stay consistent', () => {
--- jest mock history
cf21ae3 feat(server): seed script with demo data and db-check for invariants
> plan · deepseek/deepseek-v4.1-flash-1017
→ Skill "openspec-propose" 
> plan · deepseek/deepseek-v4.1-flash-1017
$ find .opencode/skills -maxdepth 3 -type f | head -50; echo '---'; grep -rn "ADDED Requirements\|## Purpose\|Requirement:" .opencode/skills 2>/dev/null | head -20
.opencode/skills/openspec-explore/SKILL.md
.opencode/skills/openspec-update-change/SKILL.md
.opencode/skills/openspec-propose/SKILL.md
.opencode/skills/openspec-sync-specs/SKILL.md
.opencode/skills/openspec-apply-change/SKILL.md
.opencode/skills/openspec-archive-change/SKILL.md
---
.opencode/skills/openspec-sync-specs/SKILL.md:79:   - `## ADDED Requirements` - New requirements to add
.opencode/skills/openspec-sync-specs/SKILL.md:119:      **ADDED Requirements:**
.opencode/skills/openspec-sync-specs/SKILL.md:136:        2. the rest of the spec is well-formed (it still has a `## Purpose`);
.opencode/skills/openspec-sync-specs/SKILL.md:151:      - Deleting the file also deletes its `## Purpose`; any other section blocks
.opencode/skills/openspec-sync-specs/SKILL.md:159:      **`## Purpose` in the delta:**
.opencode/skills/openspec-sync-specs/SKILL.md:173:      - Add Purpose section: copy the delta's `## Purpose` body verbatim when it has one
.opencode/skills/openspec-sync-specs/SKILL.md:198:## Purpose
.opencode/skills/openspec-sync-specs/SKILL.md:202:## ADDED Requirements
.opencode/skills/openspec-sync-specs/SKILL.md:204:### Requirement: New Feature
.opencode/skills/openspec-sync-specs/SKILL.md:213:### Requirement: Existing Feature
.opencode/skills/openspec-sync-specs/SKILL.md:226:### Requirement: Deprecated Feature
.opencode/skills/openspec-sync-specs/SKILL.md:230:- FROM: `### Requirement: Old Name`
.opencode/skills/openspec-sync-specs/SKILL.md:231:- TO: `### Requirement: New Name`
.opencode/skills/openspec-sync-specs/SKILL.md:241:## Purpose
.opencode/skills/openspec-sync-specs/SKILL.md:246:### Requirement: New Feature
.opencode/skills/openspec-archive-change/SKILL.md:156:   - Preserve existing `## Purpose` sections completely untouched for established main specs.
.opencode/skills/openspec-archive-change/SKILL.md:157:   - For a new main spec, copy the delta `## Purpose` verbatim. Warn only if the purpose text is shorter than standard validation expects. Do not regenerate or rewrite existing authored purpose. If no usable `## Purpose` is provided, use the existing TBD Purpose behavior and warning.
.opencode/skills/openspec-archive-change/SKILL.md:158:   - Verify that no delta-style section headers (`## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`, `## RENAMED Requirements`) remain in the main spec, adhering strictly to the sync workflow formatting rules.
.opencode/skills/openspec-archive-change/SKILL.md:159:   - Requirement blocks the sync wrote or changed use `### Requirement:` headings, and their scenarios use `#### Scenario:` headings, under the spec's `## Requirements` section. Leave content the delta does not mention exactly as it is.
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read .opencode/skills/openspec-sync-specs/SKILL.md [offset=60, limit=130]
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd server && node -e "const m=require('mongoose');const s=new m.Schema({name:{type:String,required:true},place:{type:m.Schema.Types.ObjectId,required:true}});const M=m.model('T',s);const d=new M({name:null,place:new m.Types.ObjectId()});const e=d.validateSync();console.log(e?e.errors.name.kind:'no error');"
required
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd server && sed -n '1,40p' node_modules/class-validator/cjs/decorator/common/IsOptional.js; echo '--- applyIsOptional'; grep -n "applyIsOptionalDecorator" -A 8 node_modules/@nestjs/mapped-types/dist/type-helpers.utils.js | head -20
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IsOptional = exports.IS_OPTIONAL = void 0;
const ValidationTypes_1 = require("../../validation/ValidationTypes");
const ValidationMetadata_1 = require("../../metadata/ValidationMetadata");
const MetadataStorage_1 = require("../../metadata/MetadataStorage");
exports.IS_OPTIONAL = 'isOptional';
/**
 * Checks if value is missing and if so, ignores all validators.
 */
function IsOptional(validationOptions) {
    return function (object, propertyName) {
        const args = {
            type: ValidationTypes_1.ValidationTypes.CONDITIONAL_VALIDATION,
            name: exports.IS_OPTIONAL,
            target: object.constructor,
            propertyName: propertyName,
            constraints: [
                (object, value) => {
                    return object[propertyName] !== null && object[propertyName] !== undefined;
                },
            ],
            validationOptions: validationOptions,
        };
        (0, MetadataStorage_1.getMetadataStorage)().addValidationMetadata(new ValidationMetadata_1.ValidationMetadata(args));
    };
}
exports.IsOptional = IsOptional;
//# sourceMappingURL=IsOptional.js.map--- applyIsOptional
5:export function applyIsOptionalDecorator(targetClass, propertyKey) {
6-    if (!isClassValidatorAvailable()) {
7-        return;
8-    }
9-    const classValidator = require('class-validator');
10-    const decoratorFactory = classValidator.IsOptional();
11-    decoratorFactory(targetClass.prototype, propertyKey);
12-}
13-export function applyValidateIfDefinedDecorator(targetClass, propertyKey) {
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd openspec/changes/add-event-edit && for f in proposal.md specs/events/spec.md design.md tasks.md; do printf '%s: ' "$f"; head -c 3 "$f" | od -An -tx1; done; echo '--- line endings'; file proposal.md specs/events/spec.md design.md tasks.md
proposal.md:  23 20 50
specs/events/spec.md:  23 20 53
design.md:  23 20 44
tasks.md:  23 20 54
--- line endings
zsh:1: command not found: file
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd server && set -o pipefail; npx tsc --noEmit > /tmp/opencode/tsc-out.txt 2>&1; echo "tsc_exit=$?"; head -20 /tmp/opencode/tsc-out.txt; cd ..; echo '--- status'; git status --short | head -20; ls -la server/*.tsbuildinfo 2>/dev/null || echo 'no tsbuildinfo'
tsc_exit=0
--- status
 M README.md
 M server/src/events/event.controller.ts
 M server/src/events/event.service.ts
 M server/src/integrity.spec.ts
?? .opencode/
?? openspec/
?? server/src/dto/update-event.dto.ts
?? specs/
zsh:1: no matches found: server/*.tsbuildinfo
no tsbuildinfo
> plan · deepseek/deepseek-v4.1-flash-1017
✱ Grep "APP_PIPE|ValidationPipe|useGlobalPipes" in server/src · 2 matches
$ grep -rn "useGlobalPipes\|APP_PIPE\|ValidationPipe" server/src server/test 2>/dev/null; echo '--- test files'; find server -maxdepth 3 -name '*.spec.ts' -not -path '*/node_modules/*'
server/src/main.ts:1:import { ValidationPipe } from '@nestjs/common';
server/src/main.ts:9:    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
--- test files
server/src/integrity.spec.ts
server/src/files/create-cleanup.spec.ts
server/src/files/file.service.spec.ts
server/src/auth/admin.guard.spec.ts
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd server && sed -n '1,140p' node_modules/@nestjs/common/pipes/validation.pipe.js | grep -n "transform\|isNil\|undefined\|toValidate\|plainToInstance" 
23:        const { transform, disableErrorMessages, errorHttpStatusCode, expectedType, transformOptions, validateCustomDecorators, ...validatorOptions } = options;
26:        this.isTransformEnabled = !!transform;
27:        this.transformOptions = transformOptions;
35:        classTransformer = this.loadTransformer(options.transformerPackage);
41:    loadTransformer(transformerPackage) {
42:        return (transformerPackage ??
43:            (0, load_package_util_1.loadPackage)('class-transformer', 'ValidationPipe', () => require('class-transformer')));
45:    async transform(value, metadata) {
50:        if (!metatype || !this.toValidate(metadata)) {
52:                ? this.transformPrimitive(value, metadata)
57:        const isNil = value !== originalValue;
60:        let entity = classTransformer.plainToInstance(metatype, value, this.transformOptions);
76:        if (originalValue === undefined && originalEntity === '') {
78:            // a fallback is needed to revert to the original value (when undefined).
90:        if (isNil) {
91:            // if the value was originally undefined or null, revert it back
98:            ? classTransformer.classToPlain(entity, this.transformOptions)
110:    toValidate(metadata) {
116:        return !types.some(t => metatype === t) && !(0, shared_utils_1.isNil)(metatype);
118:    transformPrimitive(value, metadata) {
132:                return undefined;
134:            // Any fasly value but `undefined` will be parsed to `false`
> plan · deepseek/deepseek-v4.1-flash-1017
→ Read server/node_modules/@nestjs/common/pipes/validation.pipe.js [offset=45, limit=65]
> plan · deepseek/deepseek-v4.1-flash-1017
$ mkdir -p /tmp/opencode/tscheck && cat > /tmp/opencode/tscheck/a.ts <<'EOF'
function Dec(...args: any[]): any { return () => {}; }
class D {
  @Dec()
  readonly name: string;
  @Dec()
  readonly description?: string;
  @Dec()
  readonly place: string;
}
console.log('compiled');
EOF
cd server && npx tsc /tmp/opencode/tscheck/a.ts --target ES2023 --module commonjs --experimentalDecorators --emitDecoratorMetadata --outDir /tmp/opencode/tscheck/out --skipLibCheck; sed -n '1,80p' /tmp/opencode/tscheck/out/a.js
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
function Dec(...args) { return () => { }; }
class D {
    name;
    description;
    place;
}
__decorate([
    Dec(),
    __metadata("design:type", String)
], D.prototype, "name", void 0);
__decorate([
    Dec(),
    __metadata("design:type", String)
], D.prototype, "description", void 0);
__decorate([
    Dec(),
    __metadata("design:type", String)
], D.prototype, "place", void 0);
console.log('compiled');
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd server && npx ts-node -r tsconfig-paths/register -e "import { UpdateEventDto } from './src/dto/update-event.dto'; const d = new UpdateEventDto(); console.log('own keys:', Object.keys(d)); console.log('name in d:', 'name' in d, (d as any).name);" 2>&1 | tail -20
own keys: []
name in d: false undefined
> plan · deepseek/deepseek-v4.1-flash-1017
$ cd server && npx ts-node -r tsconfig-paths/register -e "
import 'reflect-metadata';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { UpdateEventDto } from './src/dto/update-event.dto';
(async () => {
  for (const body of [{name:'x'}, {name:null}, {place:null}, {name:''}, {place:'bad'}, {}]) {
    const dto = plainToInstance(UpdateEventDto, body);
    const errors = await validate(dto);
    console.log(JSON.stringify(body), '=> errors:', errors.map(e => e.property), 'keys:', Object.keys(dto), 'place=', (dto as any).place);
  }
})();
" 2>&1 | tail -20
{"name":"x"} => errors: [] keys: [ 'name' ] place= undefined
{"name":null} => errors: [] keys: [ 'name' ] place= undefined
{"place":null} => errors: [] keys: [ 'place' ] place= null
{"name":""} => errors: [ 'name' ] keys: [ 'name' ] place= undefined
{"place":"bad"} => errors: [ 'place' ] keys: [ 'place' ] place= bad
{} => errors: [] keys: [] place= undefined
> plan · deepseek/deepseek-v4.1-flash-1017
$ git status --short; find server -maxdepth 2 -newer server/src/events/event.service.ts -type f -not -path '*/node_modules/*' 2>/dev/null | head -20
M README.md
 M server/src/events/event.controller.ts
 M server/src/events/event.service.ts
 M server/src/integrity.spec.ts
?? .opencode/
?? openspec/
?? server/src/dto/update-event.dto.ts
?? specs/
server/dist/tsconfig.tsbuildinfo
server/src/integrity.spec.ts
> plan · deepseek/deepseek-v4.1-flash-1017
$ ls -la --time-style=full-iso server/dist/tsconfig.tsbuildinfo server/src/events/event.service.ts 2>/dev/null; echo '--- dist'; ls -la server/dist | head; echo '--- gitignore'; grep -n 'dist\|tsbuildinfo' .gitignore server/.gitignore 2>/dev/null
-rw-r--r-- 1 maksibon users 224937 2026-10-29 02:03:16.392149664 +0300 server/dist/tsconfig.tsbuildinfo
-rw-r--r-- 1 maksibon users   3569 2026-10-29 01:58:48.675794445 +0300 server/src/events/event.service.ts
--- dist
total 528
drwxr-xr-x 10 maksibon users   4096 окт 15 00:44 .
drwxr-xr-x  6 maksibon users   4096 окт 15 01:04 ..
drwxr-xr-x  2 maksibon users   4096 окт 15 00:34 auth
drwxr-xr-x  2 maksibon users   4096 окт 15 00:34 common
drwxr-xr-x  2 maksibon users   4096 окт 29 01:28 dto
-rw-r--r--  1 maksibon users    229 окт 15 00:51 error-holder.d.ts
-rw-r--r--  1 maksibon users    934 окт 15 00:51 error-holder.js
-rw-r--r--  1 maksibon users    715 окт 15 00:51 error-holder.js.map
drwxr-xr-x  2 maksibon users   4096 окт 15 00:34 events
--- gitignore
server/.gitignore:2:/dist
> plan · deepseek/deepseek-v4.1-flash-1017
$ date '+%F %T'; stat -c '%y %n' server/dist/tsconfig.tsbuildinfo server/dist/dto/update-event.dto.js 2>/dev/null; stat -c '%y %n' openspec/changes/add-event-edit/tasks.md openspec/changes/add-event-edit/evidence/review.md 2>/dev/null
2026-10-29 02:07:01
2026-10-29 02:03:16.392149664 +0300 server/dist/tsconfig.tsbuildinfo
2026-10-29 01:28:24.310843746 +0300 server/dist/dto/update-event.dto.js
2026-10-29 02:01:50.273355032 +0300 openspec/changes/add-event-edit/tasks.md
2026-10-29 02:06:30.173865795 +0300 openspec/changes/add-event-edit/evidence/review.md
> plan · deepseek/deepseek-v4.1-flash-1017
## Итог

Цель proposal совпадает с `specs/user-story-3.md`, реализация уже лежит в рабочем дереве: `PUT` в контроллере, `UpdateEventDto`, `EventService.update`, строка в README и два интеграционных теста. `npx tsc --noEmit` проходит. Изменение аддитивное: CORS уже разрешает `PUT` (`main.ts:13`), глобальный `AdminGuard` накрывает новый маршрут, схема и клиент не тронуты.

Основные пробелы — не в «счастливом пути», а в гарантиях консистентности, обработке крайних значений и в том, что тестовый стенд не воспроизводит production-валидацию.

## Пробелы

1. **Связь чистится только у старой планеты.** `event.service.ts:68-71` делает `$pull` только по `previousPlace`. Если событие уже ошибочно числится в `events` третьей планеты, после переноса оно там останется. Требование `spec.md:22` («MUST be listed only in the events of its current planet») и сценарий `spec.md:26-27` тогда не выполняются, `db-check` покажет `planet lists event, event.place is another planet`. При этом соседние операции уже рассчитаны на рассинхрон: `deleteOne` чистит через `updateMany` (`event.service.ts:78`), удаление планеты — через `$or` (`planets.service.ts:61`). Допущение «входная БД согласована» нигде не зафиксировано.

2. **Design неточно описывает риск.** `design.md:24` говорит, что риск «тот же, что у create». Но `create` при ошибке связи компенсирует запись: удаляет событие и файлы (`event.service.ts:33-39`). `update` после `save()` (`:66`) ничего не откатывает. При ошибке `$pull`/`$addToSet` рассинхрон остаётся, и `db:check` его только обнаружит. Для падения процесса риск действительно общий, для ошибки записи — нет.

3. **`null` обходит валидацию.** `PartialType` (`update-event.dto.ts:4`) навешивает `@IsOptional()`, а он игнорирует `null`. Проверено на реальном DTO: `{name: null}` и `{place: null}` проходят `validate()` без ошибок. Дальше:
   - `place: null` → `dto.place ?? ...` (`event.service.ts:57`) берёт старую планету → 200 no-op, хотя по буквальному сценарию `spec.md:18` это «place не ObjectId» и ожидается 400;
   - `name: null` → `Object.assign` (`:64`) и `save()` → Mongoose `required` → 500, а не 400. Поведение Mongoose проверил отдельно.

4. **Тестовый стенд не воспроизводит production-валидацию.** `integrity.spec.ts:36-42` создаёт приложение без `useGlobalPipes`; `ValidationPipe({ whitelist: true })` есть только в `main.ts:9`. Следствия:
   - защита `shots` из `design.md:17` не проверена: в тестах `Object.assign(event, dto)` (`event.service.ts:64`) перезапишет `shots`, если его прислать; тест `integrity.spec.ts:128-138` его не присылает;
   - сценарий 400 (`spec.md:17-19`) не автоматизирован; `tasks.md:14` оставляет его на ручную проверку, подтверждения в change нет;
   - `jest.mock('@nestjs/mapped-types')` (`integrity.spec.ts:10`) подменяет `PartialType` на identity, поэтому в тестах `UpdateEventDto` — фактически `CreateEventDto` с обязательными `name`/`place`. Если добавить настоящий pipe, тесты 2.2 (`:144-152`) начнут получать 400 вместо 404. Текущий стенд не может проверить реальный DTO без переделки.

5. **Не покрыт «счастливый» частичный сценарий.** `spec.md:12-15` требует PUT только с `name` и сохранение остальных полей. Тест `integrity.spec.ts:125-142` шлёт `name + description + place`; `link` не проверяется вообще (ни изменение, ни сохранение), `GET /events/:id` после PUT не сверяется с ответом (`spec.md:15`). 404-тест проверяет неизменность только `name` и `place` (`:151`).

6. **MUST в спеке сильнее, чем design.** `spec.md:22` требует консистентность безусловно, а `design.md:13` исключает транзакции и `design.md:24` принимает окно рассинхрона. Плюс не описан конкурентный случай: два PUT (A→B и A→C) читают один `event.place = A`; последний `save()` побеждает, но оба `$addToSet` могут оставить событие в списках B и C. Это тоже нарушает `spec.md:22`. Нужно либо ослабить формулировку до «при согласованном входе и успешной операции», либо добавить компенсацию/очистку.

7. **`tasks.md` не отражает состояние работы.** Все пункты `tasks.md:5-15` не отмечены, хотя DTO, сервис, контроллер, README и тесты уже есть в рабочем дереве. Пункт 2.3 (400 на живом сервере) без evidence; пункт 2.4: `tsc` проходит, `jest` здесь не запускался — на 27017 нет MongoDB. Это процессный, а не кодовый пробел, но приёмка по артефакту сейчас невозможна.

8. **Нарушено языковое правило OpenSpec.** `openspec/config.yaml:4-6`: артефакты на русском, заголовки и SHALL/MUST — на английском. `specs/events/spec.md` целиком английский (тексты требований и сценариев). Либо перевести, либо явно зафиксировать исключение.

9. **README противоречит сам себе и скоупу.** `README.md:152` — английская фраза в русской таблице, и описание относится только к PUT, хотя строка перечисляет GET/PUT/DELETE. `README.md:20` обещает редактирование событий в админ-панели, но proposal выносит клиент за скоуп, а в клиенте есть только create/delete (`client/lib/slices/planetSlices.ts:58-84`). Второе — не регрессия, но противоречие осталось.

10. **Content-type не зафиксирован.** У `@Put` (`event.controller.ts:32-35`) нет multipart-интерсептора, поэтому парсится только JSON. Создание события и клиент используют `FormData` (`planetSlices.ts:58-70`, `EventCreateDrawer.tsx`). Если будущий клиент пришлёт FormData, `@Body()` будет пустым, DTO пустым, и PUT вернёт 200 no-op вместо ошибки. Для текущего скоупа это допустимо, но стоит записать как допущение «PUT только JSON».

## Совместимость и не блокеры

- `@nestjs/mapped-types@12` — ESM-only, а `tsconfig.json` собирает commonjs. На Node 22/24 (Docker/Render) работает через `require(ESM)`, но `engines` в `server/package.json` не задан, а тесты маскируют пакет моком. Это было и до изменения (`UpdatePlanetDto`), но версию Node стоит зафиксировать.
- Пустой `{}` PUT возвращает 200 и обновляет `updatedAt`; спека это не описывает.
- Проверка «GET после PUT», `link`, частичное обновление и 400 не покрыты — см. пункт 5.

## Что проверено

- Прочитаны proposal/spec/design/tasks, `server/src/events/*`, `server/src/dto/*`, `main.ts`, `integrity.spec.ts`, а также `planets.service.ts`, `planets.schema.ts`, `objects.module.ts`, `main-app.module.ts`, `admin.guard.ts`, `db-check.ts`, README, package.json, Dockerfile, render.yaml и клиентские slices.
- `npx tsc --noEmit` — exit 0.
- `jest` не запускал: MongoDB на 27017 закрыта. `openspec validate` не запускал: CLI `openspec` в окружении отсутствует. Структуру delta проверил вручную: `## Purpose`, `## ADDED Requirements`, `### Requirement:`, `#### Scenario:` на месте.
- Отслеживаемые файлы не менял (`tsc` мог обновить игнорируемый `server/dist/tsconfig.tsbuildinfo`).
