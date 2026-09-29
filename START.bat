@echo off
setlocal enabledelayedexpansion

:: Set current directory to the folder containing this batch file
cd /d "%~dp0"

title CampusPulse - Main Launcher
echo =====================================================================
echo           CampusPulse: Smart Campus Occupancy & Optimization
echo                              Main Launcher
echo =====================================================================
echo.
echo [*] Starting project...
echo.

:: Check whether virtual environment already exists
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] First-time setup required. Initializing environment...
    echo.
    call setup.bat
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Setup failed with error code !errorlevel!.
        echo Application cannot start until setup completes successfully.
        echo.
        pause
        exit /b !errorlevel!
    )
    echo.
    echo [SUCCESS] Setup completed successfully!
    echo.
) else (
    echo [INFO] Virtual environment found. Setup is already completed.
)

echo [INFO] Starting application...
echo.
call run.bat

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application closed with error code %errorlevel%.
    pause
    exit /b %errorlevel%
)
