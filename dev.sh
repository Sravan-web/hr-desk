#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  HRBot Quick Start — Strategy #5: Fast-Track Deployment             ║
# ║  One script to rule them all.                                       ║
# ╚══════════════════════════════════════════════════════════════════════╝

set -e

echo "🚀 HRBot Quick Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── Step 1: Check for .env file ─────────────────────────────────────
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before running again."
    echo "   At minimum, set ANTHROPIC_API_KEY for full functionality."
    echo "   (The app will run in demo/fallback mode without it.)"
    echo ""
fi

# ─── Step 2: Start Backend ──────────────────────────────────────────
echo "🔧 Starting Backend (FastAPI + ChromaDB)..."
if lsof -t -i:8000 >/dev/null 2>&1; then
    echo "  → Stopping existing backend on port 8000..."
    kill -9 $(lsof -t -i:8000) || true
fi
cd backend

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  → Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install deps
source venv/bin/activate
pip install -q -r requirements.txt

# Start backend in background
echo "  → Starting API server on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "  → Waiting for backend health check..."
for i in {1..15}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✅ Backend is healthy!"
        break
    fi
    sleep 1
done

# ─── Step 3: Start Frontend ─────────────────────────────────────────
echo ""
echo "🎨 Starting Frontend (Vite + React)..."
if lsof -t -i:5173 >/dev/null 2>&1; then
    echo "  → Stopping existing frontend on port 5173..."
    kill -9 $(lsof -t -i:5173) || true
fi
cd frontend

# Install deps if needed
if [ ! -d "node_modules" ]; then
    echo "  → Installing Node.js dependencies..."
    npm install --legacy-peer-deps
fi

echo "  → Starting dev server on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!
cd ..

# ─── Done ────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ HRBot is running!"
echo ""
echo "  🌐 Frontend:  http://localhost:5173"
echo "  🔌 Backend:   http://localhost:8000"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo "  💚 Health:    http://localhost:8000/health"
echo ""
echo "  Press Ctrl+C to stop all services."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Trap Ctrl+C to clean up both processes
trap "echo ''; echo '🛑 Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for either to exit
wait
