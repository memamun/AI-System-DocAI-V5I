@echo off
REM Build Automation and Installer Creation Script for AI-System-DocAI V5I
REM This script cleans previous builds, runs PyInstaller, and creates the installer

setlocal EnableDelayedExpansion

echo ================================================================================
echo AI-System-DocAI V5I - Build and Installer Creation
echo ================================================================================
echo.

REM Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run launcher.bat first to create .venv
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Step 1: Clean previous builds
echo [1/4] Cleaning previous builds...
if exist "dist\" (
    rmdir /s /q dist
    echo   - Removed dist directory
)
if exist "build\" (
    rmdir /s /q build
    echo   - Removed build directory
)
echo   - Cleanup complete
echo.

REM Step 2: Run PyInstaller
echo [2/4] Building application with PyInstaller...
echo   This may take several minutes...
python -m PyInstaller AI-System-DocAI-V5I.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo Check the output above for errors
    exit /b 1
)
echo   - PyInstaller build complete
echo.

REM Step 3: Verify PyInstaller build
echo [3/4] Verifying build...
if not exist "dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe" (
    echo   ERROR: Executable not found in dist\AI-System-DocAI-V5I\
    exit /b 1
)
echo   - Executable found: dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe
echo   - Build verification complete
echo.

REM Step 4: Build Inno Setup installer
echo [4/4] Building installer with Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :build_installer
)
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    goto :build_installer
)
echo   WARNING: Inno Setup not found in standard locations
echo   Looking for ISCC.exe in PATH...
where ISCC.exe >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Inno Setup compiler (ISCC.exe) not found!
    echo   Please install Inno Setup or add ISCC.exe to PATH
    echo.
    echo   PyInstaller build completed successfully at: dist\AI-System-DocAI-V5I\
    echo   But installer was not created due to missing Inno Setup
    exit /b 1
)
set "ISCC=ISCC.exe"

:build_installer
call "%ISCC%" installer\windows_installer.iss
if errorlevel 1 (
    echo   ERROR: Inno Setup compilation failed!
    echo   Check the output above for errors
    exit /b 1
)
echo   - Installer created successfully
echo.

REM Step 5: Create release package
echo [5/5] Creating release package...
if not exist "dist\AI-System-DocAI-V5I-Setup.exe" (
    echo   WARNING: Installer not found, skipping release package creation
    exit /b 0
)

REM Create release folder
set "RELEASE_NAME=AI-System-DocAI-V5I-5I.2025-Release"
set "RELEASE_DIR=dist\%RELEASE_NAME%"
if exist "%RELEASE_DIR%" (
    rmdir /s /q "%RELEASE_DIR%"
)
mkdir "%RELEASE_DIR%"

REM Copy files to release folder
copy "dist\AI-System-DocAI-V5I-Setup.exe" "%RELEASE_DIR%\" >nul
copy "README.md" "%RELEASE_DIR%\" >nul
copy "LICENSE" "%RELEASE_DIR%\" >nul
if exist "docs\README.md" (
    mkdir "%RELEASE_DIR%\docs" 2>nul
    copy "docs\README.md" "%RELEASE_DIR%\docs\" >nul
)
echo   - Release folder created: %RELEASE_DIR%

REM Create ZIP archive
echo   - Creating ZIP archive...
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath 'dist\%RELEASE_NAME%.zip' -Force" >nul
if errorlevel 1 (
    echo   WARNING: Failed to create ZIP archive
) else (
    echo   - ZIP archive created: dist\%RELEASE_NAME%.zip
)

echo.
echo ================================================================================
echo BUILD COMPLETE!
echo ================================================================================
echo.
echo Output files:
echo   - Executable: dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe
echo   - Installer:  dist\AI-System-DocAI-V5I-Setup.exe
echo   - Release:    dist\%RELEASE_NAME%.zip
echo.
echo Next steps:
echo   1. Test the executable: dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe
echo   2. Test the installer: dist\AI-System-DocAI-V5I-Setup.exe
echo   3. Distribute: dist\%RELEASE_NAME%.zip
echo.
pause
endlocal

