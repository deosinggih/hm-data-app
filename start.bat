@echo off
REM BA HM Generator - Start Script (Windows)
REM This script starts both backend and frontend servers

cd /d "%~dp0" || exit /b 1

echo.
echo 🚀 Starting BA HM Generator...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install from https://nodejs.org/
    pause
    exit /b 1
)

REM Setup Backend
echo 📦 Setting up backend...
cd backend

if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo ✅ Backend ready
echo.
echo 🔧 Starting backend server on port 8000...

start /B cmd /c "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul

echo ✅ Backend running: http://127.0.0.1:8000
echo.

REM Setup & Start Frontend
cd ..\frontend
echo 📦 Setting up frontend...

if not exist "node_modules" (
    echo   Installing dependencies...
    call npm install -q
)

echo.
echo 🔧 Starting frontend server on port 5173...
start "BA HM Generator Frontend" cmd /k "npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ✅ BA HM Generator is running!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📱 Frontend:  http://127.0.0.1:5173
echo 🔗 Backend:   http://127.0.0.1:8000/api/health
echo.
echo Close these windows to stop the application
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

pause
