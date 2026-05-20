@echo off
setlocal

echo ============================================
echo  NeuroPulse -- Dev Environment Startup
echo ============================================
echo.

set ROOT=%~dp0..

echo [1/2] Запускаю backend (FastAPI на http://localhost:8000) ...
start "NeuroPulse Backend" cmd /k "cd /d %ROOT%\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

timeout /t 2 /nobreak > nul

echo [2/2] Запускаю frontend (Vite на http://localhost:5173) ...
start "NeuroPulse Frontend" cmd /k "cd /d %ROOT%\frontend && npm run dev"

echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API docs: http://localhost:8000/docs
echo.
echo  Закрой оба открытых окна, чтобы остановить серверы.
pause
