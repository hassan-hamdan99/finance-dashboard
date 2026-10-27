@echo off
echo Starting DashFinanceira...
echo.
echo Backend: http://localhost:8050
echo Frontend: http://localhost:5173
echo.

start "Backend" cmd /c "cd /d %~dp0 && python -m uvicorn api:app --host 0.0.0.0 --port 8050 --reload"
timeout /t 2 /nobreak >nul
start "Frontend" cmd /c "cd /d %~dp0\frontend && npm run dev"

echo.
echo Abra http://localhost:5173 no navegador
pause
