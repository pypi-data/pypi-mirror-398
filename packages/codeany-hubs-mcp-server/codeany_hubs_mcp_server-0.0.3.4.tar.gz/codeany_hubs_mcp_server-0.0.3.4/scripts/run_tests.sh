#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="${PYTHON}"
elif [[ -x "venv/bin/python" ]]; then
  PYTHON_BIN="venv/bin/python"
else
  PYTHON_BIN="python"
fi

"${PYTHON_BIN}" -m ruff check src tests
"${PYTHON_BIN}" -m mypy src
"${PYTHON_BIN}" -m pytest "$@"
