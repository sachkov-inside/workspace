#!/usr/bin/env bash
set -euo pipefail

prototype_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_directory="${1:?output directory is required}"
mkdir -p "${output_directory}"

"${prototype_root}/scripts/package.sh" "${output_directory}/packages"
node "${prototype_root}/scripts/measure.mjs" \
  "${output_directory}/packages/inside-evaluator-darwin-arm64" \
  "${prototype_root}/ts/evaluator.mts" \
  "${output_directory}/packages/inside-evaluator-typescript.tgz" \
  > "${output_directory}/measurements.json"
cat "${output_directory}/measurements.json"
