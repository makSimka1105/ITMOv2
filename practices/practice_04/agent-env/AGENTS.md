# AGENTS.md

Interactive Warhammer 40k galaxy map for a roleplay community: planets, legions and events on a custom map, with an admin panel for editing them.

## Layout

```
client/   Next.js 15 (App Router) + React 19, Redux Toolkit, better-auth, shadcn/radix, Tailwind 4 + SCSS modules
server/   NestJS 11 + Mongoose, REST API for planets / legions / events / images
docker-compose.dev.yml    local MongoDB
docker-compose.prod.yml   self-hosted stack: mongo + server + client (customer's server)
render.yaml               Render blueprint for the API (test deploy)
scripts/db-export.sh, db-import.sh   whole-state backup / restore
```

**One MongoDB holds the entire state**, on purpose: planets/legions/events (Nest, mongoose), images in GridFS bucket `images` (Nest), and better-auth's `user`/`session`/`account`/`verification` collections (Next, `mongodbAdapter` in `client/lib/auth.ts`). One `mongodump` moves everything between deployments, so do not introduce a second store (disk uploads, Postgres, S3) without a migration story.

Request flow: the browser only talks to Next. Next rewrites `/api/backend/:path*` → `${API_ORIGIN}/:path*` (`client/next.config.ts`), so API calls are same-origin and carry the better-auth cookie. Auth itself is served by Next at `/api/auth/*`.

## Local setup

```bash
docker compose -f docker-compose.dev.yml up -d

cd server && npm ci && npm run build && node dist/main   # :5000, fails fast without MONGO_URL / FRONT_URL
cd client && npm ci && npx next dev                       # :3000
```

With `REQUIRE_EMAIL_VERIFICATION=false`, sign-up logs straight in. Emails listed in `ADMIN_EMAILS` get the `ADMIN` role at sign-up (only at creation, so an existing user keeps its role). Admin controls in the UI come from `useIsAdmin()` (`client/hooks/useIsAdmin.ts`).

## Environment

`server/.env`

| var | value |
|---|---|
| `MONGO_URL` | required, `mongodb://localhost:27017/warhammer` |
| `FRONT_URL` | required, Next origin. Used for CORS and by `AdminGuard` to call `{FRONT_URL}/api/auth/get-session` |
| `PORT` | default `5000` |

`client/.env`

| var | when | value |
|---|---|---|
| `API_ORIGIN` | build time (rewrites are baked in) | Nest URL, default `http://localhost:5000` |
| `MONGO_URL` | runtime | same DB as the server |
| `BETTER_AUTH_SECRET` | runtime | `openssl rand -hex 32` |
| `BETTER_AUTH_URL` | runtime | public URL of the Next app |
| `ADMIN_EMAILS` | runtime | `;`-separated |
| `REQUIRE_EMAIL_VERIFICATION` | runtime | `false` disables verification mails, default on |
| `RESEND_API_KEY`, `EMAIL_SENDER_NAME`, `EMAIL_SENDER_ADDRESS` | runtime | only needed with verification on; Resend needs a verified domain |

`.env*` is gitignored in both packages and at the root (root `.env` feeds `docker-compose.prod.yml`, see `.env.prod.example`).

## API (server)

| method | path | notes |
|---|---|---|
| GET/POST | `/planets` | multipart, file field `pic`; `legion1`, `legion2` link legions |
| GET/PUT/DELETE | `/planets/:id` | deleting a planet deletes its events and their shots |
| GET/POST | `/legions` | file field `icon` |
| GET/PUT/DELETE | `/legions/:id` | |
| GET/POST | `/events` | file field `shots` (≤4), `place` = planet id |
| GET/DELETE | `/events/:id` | no PUT |
| DELETE | `/planets`, `/legions`, `/events` | wipes the whole collection |
| GET | `/files/:name` | image from GridFS, `name` = `<objectId>.<ext>`, immutable cache headers |

Writes are admin-only: the global `AdminGuard` (`server/src/auth/admin.guard.ts`) passes GET/HEAD/OPTIONS and otherwise forwards the request cookie to `{FRONT_URL}/api/auth/get-session`, answering 401 without a session and 403 without the `ADMIN` role. Every client API call goes through `client/lib/api.ts` (`baseURL: "/api/backend"`, `withCredentials`), never bare `axios`.

DTOs are validated by a global `ValidationPipe` (whitelist + transform); bad ObjectIds in params give 400. Uploads go through `imageUploadOptions` (`server/src/files/upload.options.ts`): png/jpeg/webp only (else 400), at most 4 MB (else 413). The 4 MB limit stays under Vercel's 4.5 MB request body cap. Stored values are `<objectId>.<ext>`, and the client builds URLs with `fileUrl()` (`client/lib/fileUrl.ts`).

## Checks

Before claiming a change works:

```bash
cd server && npx --no-install tsc --noEmit && npm test && npm run build   # jest needs the local Mongo
cd client && npx --no-install tsc --noEmit && npm run build
```

Run `npx tsc` only from inside a package. From the repo root it pulls an unrelated npm package called `tsc`.

API changes: run the `smoke-api` skill (`.claude/skills/smoke-api`). Inspect Mongo data through the read-only `mongodb` MCP server (`.mcp.json`, pass `connectionId: "preconfigured"`) instead of ad-hoc scripts. GridFS consistency (files nobody references, references to missing files) is the `image_refs` tool of the `image-refs` MCP server (`mcp/image-refs/server.js`), also read-only.

## Known problems

- A failed document insert no longer orphans uploads (`create` in planets/legions/events cleans up). Still open: if one of several event shots fails to upload, `uploadFiles` (`Promise.all`) leaves the others in GridFS, and a failed `legion.save()` after a planet insert is not rolled back. `image_refs` finds such files.
- `client/lib/auth.ts` falls back to `mongodb://localhost:27017/warhammer` when `MONGO_URL` is unset (the docker build has no env), so a misconfigured deployment shows up as a connection error at runtime.
- `DELETE /planets|/legions|/events` wipe whole collections. They are admin-only, but have no UI and no confirmation.
- Events have no PUT.

## Conventions

- TypeScript everywhere. Client components live in `client/components/<area>/`, domain types in `client/app/types/`, server state in Redux slices.
- Styling: SCSS modules in `client/app/styles/` for the map and custom UI, shadcn components in `client/components/ui/`.
- Server modules follow Nest layout: `<entity>.controller.ts`, `<entity>.service.ts`, `<entity>.schema.ts`, DTOs in `server/src/dto/`.
- Server code: 4-space indent, single quotes in new files, Nest exceptions (`NotFoundException`, `BadRequestException`, …) instead of `throw Error`, so clients get a real status.
- Client code: double quotes, function components, API calls only through Redux thunks that use `api` from `client/lib/api.ts`, image URLs only through `fileUrl()`.
- New behaviour comes with a test: `*.spec.ts` next to the server file (jest, `npm test` in `server/`).
- Keep diffs surgical: touch only what the task needs, leave unrelated formatting alone. Comments explain *why*, in Russian or English.
- Conventional commits (`feat(server): …`, `fix(client): …`). Do not commit, push or open PRs unless asked.

`.claude/hooks/check-edit.sh` runs after every edit of a `client/` or `server/src/` TS file. It typechecks that package and rejects bare `axios` imports in the client. If the hook fails, fix the error before moving on. Both packages typecheck clean today, so any error is yours.

## Deployments

- Test: Vercel (client, root `client/`, env incl. `API_ORIGIN` before the first build) + Render free (server, `render.yaml`) + MongoDB Atlas M0. Render sleeps after 15 min idle, and the first request takes about a minute.
- Customer's server: `docker-compose.prod.yml` with root `.env` from `.env.prod.example`. The compose project is pinned to `warhammer-prod`, and `scripts/db-import.sh --compose` targets its mongo service.
- Moving data: `scripts/db-export.sh '<source uri>' backups/x.archive.gz`, then `scripts/db-import.sh --compose backups/x.archive.gz` (drops and replaces the same collections). Keep the DB name `warhammer` everywhere, or pass source/target DB names to the import script. Backups on the customer's server: `scripts/db-export.sh --compose`.
