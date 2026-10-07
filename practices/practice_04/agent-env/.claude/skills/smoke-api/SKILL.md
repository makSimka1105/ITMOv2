---
name: smoke-api
description: Smoke-test the running API as anonymous, user and admin. Use after changing server controllers, guards, uploads or the Next proxy, or before claiming an API change works.
---

# Smoke-test the API

The stack must be up (see AGENTS.md "Local setup"): Nest on :5000, Next on :3000 with `REQUIRE_EMAIL_VERIFICATION=false`. Check with `curl -sf localhost:3000/api/backend/planets`. Go through the Next proxy (`/api/backend`), the same path the browser takes.

## 1. Get sessions

```bash
B=http://localhost:3000
for who in admin user; do
  curl -s -o /dev/null -H 'Content-Type: application/json' -H "Origin: $B" \
    -d "{\"name\":\"$who\",\"email\":\"$who@local.test\",\"password\":\"${who}12345\"}" $B/api/auth/sign-up/email
  curl -s -o /dev/null -c /tmp/wh-$who.jar -H 'Content-Type: application/json' -H "Origin: $B" \
    -d "{\"email\":\"$who@local.test\",\"password\":\"${who}12345\"}" $B/api/auth/sign-in/email
done
```

`admin@local.test` must be in `ADMIN_EMAILS`. The role is assigned at sign-up only.

## 2. Hit the endpoints

For each changed endpoint, record the status for anonymous, user (`-b /tmp/wh-user.jar`) and admin (`-b /tmp/wh-admin.jar`):

```bash
curl -s -o /tmp/wh-out -w '%{http_code}\n' -b /tmp/wh-admin.jar -F name=Smoke -F description=x \
  -F 'icon=@client/public/assets_project_map_pngs/main/segments_all.png;type=image/png' $B/api/backend/legions
```

Reads stay public. Writes return 401 for anonymous, 403 for a user, 2xx for an admin. Images from responses must load through `$B/api/backend/files/<value>` with `image/*` Content-Type.

## 3. Clean up

Delete everything you created by id (`DELETE $B/api/backend/legions/<id>` as admin). The `mongodb` MCP server is read-only: use its `find` with `connectionId: "preconfigured"` (without it the tool fails validation) on `legions` / `planets` / `events` to confirm the rows are gone. Then call `image_refs` from the `image-refs` MCP server: `orphans` and `dangling` must both be empty.

Done when every changed endpoint has the expected status for all three roles and the smoke rows are deleted and `image_refs` reports no orphans.
