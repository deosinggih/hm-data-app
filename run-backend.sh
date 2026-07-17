#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/backend"

PORT="${PORT:-8000}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -r requirements.txt
else
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Jika port sudah dipakai proses hm-data-app, biarkan saja
if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  echo "Backend sudah berjalan di http://127.0.0.1:${PORT}"
  curl -sS "http://127.0.0.1:${PORT}/api/health"
  echo
  exit 0
fi

# Jika port terpakai proses lain, geser ke 8001
if lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port ${PORT} terpakai. Mencoba 8001..."
  PORT=8001
fi

echo "Starting backend on http://127.0.0.1:${PORT}"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port "${PORT}"