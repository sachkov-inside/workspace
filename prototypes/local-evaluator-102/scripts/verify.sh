#!/usr/bin/env bash
set -euo pipefail

prototype_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
check_directory="$(mktemp -d "${TMPDIR:-/tmp}/inside-evaluator-check.XXXXXX")"
trap 'rm -rf "${check_directory}"' EXIT

"${prototype_root}/prototype" go pass "${check_directory}/go-pass"
"${prototype_root}/prototype" typescript pass "${check_directory}/typescript-pass"

if "${prototype_root}/prototype" go bad-signature "${check_directory}/go-failure"; then
  echo "bad-signature fixture unexpectedly passed" >&2
  exit 1
fi
node "${prototype_root}/platform/assert-failure.mts" "${check_directory}/go-failure/report.json"

node "${prototype_root}/platform/contract-checks.mts" \
  "${check_directory}/go-pass/report.json" \
  "${check_directory}/go-pass/source-snapshot.json" \
  "${prototype_root}/case-spec.json" \
  "${prototype_root}/assignment.json"

echo "all local evaluator prototype checks passed"
