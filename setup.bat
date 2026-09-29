@echo off
setlocal enabledelayedexpansion

:: Ensure we are running in the script's directory
cd /d "%~dp0"

title CampusPulse - Initial Setup
echo =====================================================================
echo           CampusPulse: Smart Campus Occupancy ^& Optimization
echo                       Environment Setup Script
echo =====================================================================
echo.

:: 1. Check Python installation
echo [*] Checking Python installation...
set "PY_CMD=python"
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py -V >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=py -3"
    ) else (
        echo [ERROR] Python was not found in PATH!
        echo Please install Python 3.11+ from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

%PY_CMD% --version
echo [OK] Python is installed and verified.
echo.

:: 2. Create Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment venv...
    %PY_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo [OK] Virtual environment venv already exists.
)
echo.

:: 3. Activate Virtual Environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated.
echo.

:: 4. Upgrade pip and install dependencies
echo [*] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [*] Installing required packages from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Package installation failed!
    pause
    exit /b 1
)
echo [OK] All dependencies installed successfully.
echo.

:: 5. Verify / Train ML Models
if not exist "ml\models\occupancy_model.pkl" (
    echo [*] Serialized ML models not found. Training baseline models...
    python ml\train_model.py
    if !errorlevel! neq 0 (
        echo [WARNING] Model training encountered an issue, but continuing...
    ) else (
        echo [OK] ML models trained and saved to ml/models/
    )
) else (
    echo [OK] ML model artifacts found in ml/models/.
)
echo.

:: 6. Initialize and Seed Database
echo [*] Initializing and verifying database...
python -m backend.seed
if %errorlevel% neq 0 (
    echo [WARNING] Database seeding returned an issue, but database will initialize on server boot.
) else (
    echo [OK] Database verified and ready.
)
echo.

:: 7. Run Verification Tests
echo [*] Running automated tests to ensure system integrity...
python -m pytest tests/ -q
if %errorlevel% neq 0 (
    echo [WARNING] Some tests did not pass. Check test logs.
) else (
    echo [OK] All automated tests passed successfully!
)
echo.

echo =====================================================================
echo                    SETUP COMPLETED SUCCESSFULLY!
echo =====================================================================
echo.
echo You can now start the application anytime by double-clicking:
echo      run.bat   OR   START.bat
echo.
pause
