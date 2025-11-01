@echo off
REM Verify Inno Setup Installer Setup
REM This script checks if all prerequisites are met before building the installer

echo ============================================================
echo AI-System-DocAI V5I - Installer Setup Verification
echo ============================================================
echo.

set ERROR_COUNT=0

REM Check if PyInstaller build exists
echo [1] Checking PyInstaller build...
if exist "..\dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe" (
    echo     [OK] Main executable found
) else (
    echo     [ERROR] Main executable not found!
    echo     Expected: ..\dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe
    echo     Please run: pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
    set /a ERROR_COUNT+=1
)

REM Check if src directory exists in build
echo [2] Checking src directory...
if exist "..\dist\AI-System-DocAI-V5I\src" (
    echo     [OK] src directory found
) else (
    echo     [ERROR] src directory not found in build!
    set /a ERROR_COUNT+=1
)

REM Check if assets directory exists
echo [3] Checking assets directory...
if exist "..\assets\app-icon.ico" (
    echo     [OK] Icon file found
) else (
    echo     [WARNING] Icon file not found: ..\assets\app-icon.ico
    echo     Installer will work but may not have an icon
)

REM Check if README exists
echo [4] Checking documentation...
if exist "..\README.md" (
    echo     [OK] README.md found
) else (
    echo     [WARNING] README.md not found
)

REM Check if LICENSE exists
if exist "..\LICENSE" (
    echo     [OK] LICENSE found
) else (
    echo     [WARNING] LICENSE not found
)

REM Check if Inno Setup is installed
echo [5] Checking Inno Setup...
where iscc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     [OK] Inno Setup Compiler (iscc) found in PATH
) else (
    echo     [WARNING] Inno Setup Compiler not found in PATH
    echo     You may need to use full path or Inno Setup GUI
    echo     Expected: C:\Program Files (x86)\Inno Setup 6\ISCC.exe
)

echo.
echo ============================================================
if %ERROR_COUNT% EQU 0 (
    echo Verification PASSED - Ready to build installer!
    echo.
    echo To build the installer, run:
    echo   iscc installer\windows_installer.iss
    echo.
    echo Or open installer\windows_installer.iss in Inno Setup Compiler
) else (
    echo Verification FAILED - %ERROR_COUNT% error(s) found
    echo Please fix the errors above before building the installer
)
echo ============================================================
echo.

pause

