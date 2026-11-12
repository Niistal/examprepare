#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -x .venv/bin/python ]]; then
    .venv/bin/python -m http.server 8080 --bind 127.0.0.1
else
    python3 -m http.server 8080 --bind 127.0.0.1
fi
