#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  if command -v python3.11 >/dev/null 2>&1; then PYTHON=python3.11; else PYTHON=python3; fi
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-study.txt
.venv/bin/python -c 'import numpy,pandas,matplotlib,sklearn;print("Entorno Python OK")'
echo 'Entorno listo. Activa con: source .venv/bin/activate'
