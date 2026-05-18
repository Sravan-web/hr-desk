"""
run.py — Uvicorn launcher that ensures the backend directory is on sys.path.
Usage: python run.py
"""
import sys
import os

# Ensure this file's directory is always on the path BEFORE importing app
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Now import the app object directly (avoids string-based import issues)
from main import app  # noqa: E402

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
