#!/bin/bash

# BA HM Generator - Start Script (Mac/Linux)
# This script starts both backend and frontend servers

cd "$(dirname "$0")" || exit 1

echo "🚀 Starting BA HM Generator..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install from https://nodejs.org/"
    exit 1
fi

# Setup Backend
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "✅ Backend ready"

# Start Backend
echo "🔧 Starting backend server on port 8000..."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 2

# Check backend health
if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend running: http://127.0.0.1:8000"
else
    echo "⚠️  Backend might not be ready yet..."
fi

echo ""

# Setup & Start Frontend
cd ../frontend
echo "📦 Setting up frontend..."

if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install -q
fi

echo "🔧 Starting frontend server on port 5173..."
npm run dev &
FRONTEND_PID=$!
sleep 2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ BA HM Generator is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend:  http://127.0.0.1:5173"
echo "🔗 Backend:   http://127.0.0.1:8000/api/health"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cleanup on exit
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Goodbye!'" EXIT

# Keep script running
wait
