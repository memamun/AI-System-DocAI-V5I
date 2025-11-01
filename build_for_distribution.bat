@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo AI-System-DocAI V5I - Distribution Build Script
echo ============================================================
echo.

set VERSION=5I.2025
set RELEASE_NAME=AI-System-DocAI-V5I-%VERSION%-Release

echo [1] Cleaning previous builds...
if exist dist rd /s /q dist 2>nul
if exist build rd /s /q build 2>nul
if exist "%RELEASE_NAME%" rd /s /q "%RELEASE_NAME%" 2>nul
if exist "%RELEASE_NAME%.zip" del /q "%RELEASE_NAME%.zip" 2>nul
echo     [OK] Cleaned
echo.

echo [2] Building PyInstaller application...
pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
if errorlevel 1 (
    echo     [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)
echo     [OK] PyInstaller build complete
echo.

echo [3] Verifying installer prerequisites...
call installer\verify_installer_setup.bat
if errorlevel 1 (
    echo     [WARNING] Some prerequisites may be missing, but continuing...
    echo     Please review warnings above
)
echo.

echo [4] Building installer...
iscc installer\windows_installer.iss
if errorlevel 1 (
    echo     [ERROR] Installer build failed!
    pause
    exit /b 1
)
echo     [OK] Installer built
echo.

echo [5] Creating release package...
mkdir "%RELEASE_NAME%" 2>nul
copy dist\AI-System-DocAI-V5I-Setup.exe "%RELEASE_NAME%\" >nul 2>&1
if not exist "%RELEASE_NAME%\AI-System-DocAI-V5I-Setup.exe" (
    echo     [ERROR] Failed to copy installer!
    pause
    exit /b 1
)

if exist README.md copy README.md "%RELEASE_NAME%\" >nul 2>&1
if exist LICENSE copy LICENSE "%RELEASE_NAME%\" >nul 2>&1
if exist docs\INSTALL.md copy docs\INSTALL.md "%RELEASE_NAME%\INSTALLATION_INSTRUCTIONS.md" >nul 2>&1

echo     [OK] Release package created
echo.

echo [6] Creating ZIP archive...
powershell -Command "Compress-Archive -Path '%RELEASE_NAME%' -DestinationPath '%RELEASE_NAME%.zip' -Force" 2>nul
if errorlevel 1 (
    echo     [WARNING] ZIP creation failed - manual compression may be needed
    echo     Release folder ready: %RELEASE_NAME%\
) else (
    echo     [OK] ZIP archive created: %RELEASE_NAME%.zip
)
echo.

echo ============================================================
echo Build Complete!
echo ============================================================
echo.
echo Distribution files:
echo   - Installer: dist\AI-System-DocAI-V5I-Setup.exe
echo   - Release package: %RELEASE_NAME%\
if exist "%RELEASE_NAME%.zip" (
    echo   - ZIP archive: %RELEASE_NAME%.zip
)
echo.
echo Ready for distribution!
echo.
echo Next steps:
echo   1. Test installer on clean system
echo   2. Verify all files in release package
echo   3. Upload to distribution channel
echo.
pause


