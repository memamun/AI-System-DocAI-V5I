@echo off
REM Windows Launcher for AI-System-DocAI V5I
REM Handles venv setup and application launch

setlocal enabledelayedexpansion

echo ============================================================
echo AI-System-DocAI V5I - Enterprise Edition (Windows)
echo ============================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check for Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PY_VERSION=%%i"
echo [INFO] Python version: %PY_VERSION%

REM Create logs directory
if not exist "logs" mkdir "logs"

REM Log startup
set "LOG_FILE=logs\AI-System-DocAI_Startup.log"
echo ================================================================================ >> "%LOG_FILE%"
echo AI-System-DocAI V5I - Windows Launcher >> "%LOG_FILE%"
echo Timestamp: %date% %time% >> "%LOG_FILE%"
echo Python Version: %PY_VERSION% >> "%LOG_FILE%"
echo ================================================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Check for virtual environment
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment found
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check for requirements.txt
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

REM Install/upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install dependencies
echo [INFO] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some dependencies failed to install
)

echo.
echo [INFO] Launching AI-System-DocAI...
echo ============================================================
echo.

REM Launch the application
python main.py

REM Deactivate virtual environment
deactivate

echo.
echo ============================================================
echo Application closed
echo ============================================================
pause

