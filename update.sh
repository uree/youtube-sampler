#!/usr/bin/env bash
set -euo pipefail

APP_LOCATION="${1:?Usage: $0 <app-folder>}"

cd "$APP_LOCATION"

docker compose -f compose.yml -f compose.prod.yml up -d --build flask