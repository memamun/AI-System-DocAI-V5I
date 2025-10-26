@echo off
REM Windows script to download embedding model for AI-System-DocAI
echo ============================================================
echo AI-System-DocAI - Model Download
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Download the model
python download_model.py

echo.
echo Press any key to exit...
pause >nul

