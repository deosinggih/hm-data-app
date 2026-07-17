#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/frontend"

API_PORT="${API_PORT:-8000}"
if ! curl -fsS "http://127.0.0.1:${API_PORT}/api/health" >/dev/null 2>&1; then
  if curl -fsS "http://127.0.0.1:8001/api/health" >/dev/null 2>&1; then
    API_PORT=8001
  else
    echo "WARNING: Backend belum terdeteksi di :8000/:8001"
    echo "Jalankan dulu: bash ../run-backend.sh"
  fi
fi

# Pastikan proxy Vite mengarah ke API yang hidup
export VITE_API_PROXY_TARGET="http://127.0.0.1:${API_PORT}"

if [[ ! -d node_modules ]]; then
  npm install
fi

echo "Frontend → http://127.0.0.1:5173  (API proxy → ${VITE_API_PROXY_TARGET})"
exec npm run dev -- --host 127.0.0.1 --port 5173