#!/usr/bin/env bash
set -euo pipefail

prototype_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_directory="${1:?output directory is required}"
mkdir -p "${output_directory}"

(
  cd "${prototype_root}/go"
  env CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 \
    go build -trimpath -ldflags='-s -w' -o "${output_directory}/inside-evaluator-darwin-arm64" .
  env CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags='-s -w' -o "${output_directory}/inside-evaluator-linux-amd64" .
)

tar -czf "${output_directory}/inside-evaluator-typescript.tgz" \
  -C "${prototype_root}/ts" evaluator.mts

"${output_directory}/inside-evaluator-darwin-arm64" version
node "${prototype_root}/ts/evaluator.mts" version

if docker run --rm --platform linux/amd64 \
  -v "${output_directory}:/artifacts:ro" \
  alpine:3.22 \
  /artifacts/inside-evaluator-linux-amd64 version; then
  echo "verified Go runtime on Linux amd64"
else
  echo "UNCONFIRMED: this arm64 Docker host cannot execute Linux amd64 images" >&2
fi
if docker run --rm --platform linux/amd64 \
  -v "${prototype_root}/ts:/prototype:ro" \
  node:22-alpine \
  node /prototype/evaluator.mts version; then
  echo "verified TypeScript runtime on Linux amd64"
else
  echo "UNCONFIRMED: TypeScript Linux amd64 runtime needs an amd64-capable host" >&2
fi

file "${output_directory}/inside-evaluator-darwin-arm64"
file "${output_directory}/inside-evaluator-linux-amd64"
du -h "${output_directory}"/*
