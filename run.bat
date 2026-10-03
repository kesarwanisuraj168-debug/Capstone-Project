@echo off
setlocal enabledelayedexpansion

:: Always run from the folder that contains this script
cd /d "%~dp0"

title CampusPulse - Server Runtime
echo =====================================================================
echo           CampusPulse: Smart Campus Occupancy & Optimization
echo                              Web Server
echo =====================================================================
echo.

:: 1. Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [WARNING] Virtual environment 'venv' was not found!
    echo It looks like this is the first time you are running the project.
    echo.
    echo Running setup.bat automatically now...
    echo.
    call setup.bat
    if %errorlevel% neq 0 (
        echo [ERROR] Setup failed! Please run setup.bat manually.
        pause
        exit /b 1
    )
)

:: 2. Activate virtual environment
call venv\Scripts\activate.bat

:: 3. Display Connection Details
echo.
echo =====================================================================
echo  SERVER STARTING AT:
echo    - Web Application:    http://localhost:8000/
echo    - Interactive API Docs: http://localhost:8000/docs
echo    - API Health Check:   http://localhost:8000/api/health
echo.
echo  DEMO CREDENTIALS:
echo    - Administrator:      admin / admin123
echo    - Standard User:      user / user123
echo.
echo  Press Ctrl+C anytime to stop the server.
echo =====================================================================
echo.

:: 4. Automatically open browser in 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000/"

:: 5. Launch FastAPI backend via Uvicorn
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server terminated unexpectedly.
    pause
)
