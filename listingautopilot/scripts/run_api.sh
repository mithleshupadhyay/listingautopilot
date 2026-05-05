#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONPATH="${PWD}/src:${PYTHONPATH:-}"

UVICORN_BIN="${UVICORN_BIN:-uvicorn}"
if [ -x "../.venv/bin/uvicorn" ]; then
  UVICORN_BIN="../.venv/bin/uvicorn"
fi

"${UVICORN_BIN}" listingautopilot.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
