#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5vl:3b}"
export OLLAMA_MODEL

command -v ollama >/dev/null || { echo "Ollama not found: https://ollama.com/download"; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 not found."; exit 1; }

# Start Ollama if it isn't already running in the background
curl -s http://localhost:11434/api/tags >/dev/null 2>&1 || { ollama serve >/dev/null 2>&1 & sleep 3; }

echo "[1/3] Checking model: $OLLAMA_MODEL (first run downloads ~3 GB)"
ollama pull "$OLLAMA_MODEL"

echo "[2/3] Installing Python packages"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[3/3] Starting app: http://localhost:8000"
( sleep 2; (open http://localhost:8000 || xdg-open http://localhost:8000) >/dev/null 2>&1 ) &
uvicorn backend.app:app --port 8000
