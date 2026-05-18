#!/bin/bash
# Backend start script — sets PYTHONPATH so uvicorn reloader subprocess can find modules
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR"
exec "$SCRIPT_DIR/venv/bin/python3" -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir "$SCRIPT_DIR"
