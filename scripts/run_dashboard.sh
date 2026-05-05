#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONPATH="${PWD}/src:${PYTHONPATH:-}"

STREAMLIT_BIN="${STREAMLIT_BIN:-streamlit}"
if [ -x ".venv/bin/streamlit" ]; then
  STREAMLIT_BIN=".venv/bin/streamlit"
fi

"${STREAMLIT_BIN}" run dashboard/streamlit_app.py
