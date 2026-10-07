#!/usr/bin/env bash
# PostToolUse: typecheck the package an edited TS file belongs to and enforce
# repo rules. Exit 2 sends stderr back to the agent.
set -uo pipefail

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[[ -z "$file" ]] && exit 0

rel="${file#"$root"/}"
case "$rel" in
  client/*.ts | client/*.tsx) pkg=client ;;
  server/src/*.ts) pkg=server ;;
  *) exit 0 ;;
esac

problems=""

if [[ $pkg == client && $rel != client/lib/api.ts ]] &&
  grep -qE "from ['\"]axios['\"]" "$file"; then
  problems+="$rel imports axios directly. Use { api } from \"@/lib/api\" so requests carry the session cookie."$'\n'
fi

if ! out=$(cd "$root/$pkg" && npx --no-install tsc --noEmit 2>&1); then
  problems+="tsc failed in $pkg/:"$'\n'"$(grep 'error TS' <<<"$out" | head -20)"$'\n'
fi

if [[ -n "$problems" ]]; then
  printf '%s' "$problems" >&2
  exit 2
fi
