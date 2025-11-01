@echo off
REM Build script for AI-System-DocAI V5I executable
REM Creates a packaged Windows executable using PyInstaller

echo ========================================
echo AI-System-DocAI V5I - Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

echo [1/3] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "AI-System-DocAI-V5I.spec" (
    echo Using existing spec file: AI-System-DocAI-V5I.spec
) else (
    echo ERROR: Spec file not found!
    echo Please ensure AI-System-DocAI-V5I.spec exists in the current directory.
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable with PyInstaller...
echo This may take 5-15 minutes depending on your system...
echo.

pyinstaller --clean AI-System-DocAI-V5I.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo Executable location:
if exist "dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe" (
    echo   dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe (onedir mode)
) else if exist "dist\AI-System-DocAI-V5I.exe" (
    echo   dist\AI-System-DocAI-V5I.exe (onefile mode)
) else (
    echo   ERROR: Executable not found in expected location!
)

echo.
echo IMPORTANT NOTES:
echo - First run will download embedding model (~90MB) if not cached
echo - Executable size will be large (500MB-1GB) - this is normal for ML apps
echo - Test on a clean Windows system to ensure all dependencies are included
echo - Antivirus may flag the executable (false positive) due to large size
echo.
pause

