@echo off
echo Starting Synapse Mind - All Components
echo.
echo Starting Backend...
start cmd /k "call start-backend.bat"
timeout /t 3 >nul
echo.
echo Starting Frontend...
start cmd /k "call start-frontend.bat"
echo.
echo All components started!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Extension: Load from chrome://extensions/
echo.
pause
