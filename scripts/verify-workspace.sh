#!/usr/bin/env bash
set -euo pipefail

project_root=$(git rev-parse --show-toplevel)

required_files=(
  "AGENTS.md"
  "CONTEXT.md"
  "docs/agents/issue-tracker.md"
  "docs/agents/testing-profile.md"
  "docs/agents/review-profile.md"
  ".out-of-scope/README.md"
  ".harness/harness.lock"
)

for required_file in "${required_files[@]}"; do
  test -f "$project_root/$required_file"
done

if rg -n '\{\{[^}]+\}\}' "$project_root/AGENTS.md" "$project_root/docs"; then
  echo "Unresolved harness template markers found" >&2
  exit 1
fi

rg -q '^provider: github$' "$project_root/docs/agents/issue-tracker.md"
rg -q '^project: KirillSachkov/sachkov-inside$' "$project_root/docs/agents/issue-tracker.md"
git -C "$project_root" diff --check

brain_root_tool=""
for candidate in \
  "${SACHKOV_BRAIN:-}/harness/bin/brain-root" \
  "$HOME/Work/sachkov-os/harness/bin/brain-root" \
  "$HOME/dev/brain/harness/bin/brain-root"; do
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    brain_root_tool="$candidate"
    break
  fi
done

if [[ -z "$brain_root_tool" ]]; then
  echo "Cannot resolve canonical brain-root tool" >&2
  exit 1
fi

brain_path=$($brain_root_tool)
python3 "$brain_path/harness/bin/harness" diff "$project_root"
