# Distribution Guide - AI-System-DocAI V5I

## 🚀 Distribution Workflow

### Phase 1: Pre-Distribution Checklist

Before distributing, complete all these steps:

#### 1. Final Testing
- [ ] Run `python test_packaging.py` - all tests pass
- [ ] Build PyInstaller application successfully
- [ ] Build Inno Setup installer successfully
- [ ] Test installer on clean Windows VM
- [ ] Verify application runs after installation
- [ ] Test all features (indexing, querying, LLM backends)
- [ ] Test uninstallation

#### 2. Version Verification
- [ ] Version number correct in all files:
  - `pyproject.toml`
  - `installer/windows_installer.iss`
  - `src/config.py`
- [ ] Build date/version in application
- [ ] README updated with current version

#### 3. Documentation
- [ ] README.md is up to date
- [ ] User guide complete (if applicable)
- [ ] Changelog/Release notes prepared
- [ ] License file included

### Phase 2: Build Distribution Package

#### Step 1: Clean Previous Builds
```batch
REM Clean previous builds
rd /s /q dist
rd /s /q build
del /q *.spec.bak
```

#### Step 2: Build PyInstaller Application
```batch
REM Build with PyInstaller
pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
```

**Expected output**: `dist/AI-System-DocAI-V5I/` directory with all files

**Verify**:
- ✅ `AI-System-DocAI-V5I.exe` exists
- ✅ `src/` directory included
- ✅ `assets/` directory included
- ✅ All DLLs present
- ✅ Size: ~500MB-1GB (normal for ML apps)

#### Step 3: Verify Installer Prerequisites
```batch
REM Run verification script
installer\verify_installer_setup.bat
```

**Should show**: "Verification PASSED - Ready to build installer!"

#### Step 4: Build Installer
```batch
REM Build Windows installer
iscc installer\windows_installer.iss
```

**Expected output**: `dist/AI-System-DocAI-V5I-Setup.exe`

**Verify**:
- ✅ Installer builds without errors
- ✅ Installer size: ~500MB-1GB
- ✅ Installer runs and shows wizard

#### Step 5: Create Distribution Package

**For Enterprise Distribution:**
```
AI-System-DocAI-V5I-Release/
├── AI-System-DocAI-V5I-Setup.exe    (Installer)
├── README.md                         (User guide)
├── LICENSE                           (License file)
├── CHANGELOG.md                      (Release notes)
└── INSTALLATION_INSTRUCTIONS.md      (Installation guide)
```

**For Portable Distribution:**
```
AI-System-DocAI-V5I-Portable.zip
├── AI-System-DocAI-V5I/              (Extracted from dist/)
│   ├── AI-System-DocAI-V5I.exe
│   ├── src/
│   ├── assets/
│   └── ...
└── README.md
```

### Phase 3: Create Release Package

#### Option A: Enterprise Installer (Recommended)

**Files to include:**
1. **AI-System-DocAI-V5I-Setup.exe** - Main installer
2. **README.md** - User documentation
3. **LICENSE** - License file
4. **INSTALLATION_INSTRUCTIONS.md** - Step-by-step guide
5. **CHANGELOG.md** - Version history

**Create release folder:**
```batch
mkdir AI-System-DocAI-V5I-5I.2025-Release
copy dist\AI-System-DocAI-V5I-Setup.exe AI-System-DocAI-V5I-5I.2025-Release\
copy README.md AI-System-DocAI-V5I-5I.2025-Release\
copy LICENSE AI-System-DocAI-V5I-5I.2025-Release\
copy docs\INSTALL.md AI-System-DocAI-V5I-5I.2025-Release\INSTALLATION_INSTRUCTIONS.md
```

**Create ZIP for distribution:**
```batch
REM Compress release package
powershell Compress-Archive -Path AI-System-DocAI-V5I-5I.2025-Release -DestinationPath AI-System-DocAI-V5I-5I.2025-Release.zip
```

#### Option B: Portable Version

```batch
REM Create portable package
xcopy dist\AI-System-DocAI-V5I portable\AI-System-DocAI-V5I\ /E /I
copy README.md portable\
copy LICENSE portable\
powershell Compress-Archive -Path portable -DestinationPath AI-System-DocAI-V5I-5I.2025-Portable.zip
```

### Phase 4: Distribution Channels

#### 1. Internal/Enterprise Distribution

**Recommended Channels:**
- Network share
- Internal software repository
- Enterprise software deployment system
- Email distribution (for small teams)
- Intranet download page

**Distribution Package:**
- Single installer file: `AI-System-DocAI-V5I-Setup.exe`
- Optional: ZIP with installer + documentation

#### 2. Public Distribution (if applicable)

**Options:**
- GitHub Releases
- Software download sites
- Direct download links
- Cloud storage (OneDrive, Google Drive, etc.)

### Phase 5: Release Checklist

#### Pre-Release
- [ ] All tests passing
- [ ] Version numbers updated
- [ ] Documentation finalized
- [ ] Build completed successfully
- [ ] Installer tested on clean system
- [ ] Release notes prepared

#### Release Files
- [ ] Installer: `AI-System-DocAI-V5I-Setup.exe`
- [ ] README.md
- [ ] LICENSE
- [ ] CHANGELOG.md or Release Notes
- [ ] Installation instructions

#### Post-Release
- [ ] Distribution links verified
- [ ] Download available
- [ ] Users notified (if applicable)
- [ ] Support channels ready

## 📦 Distribution Package Structure

### Minimal Distribution (Installer Only)
```
AI-System-DocAI-V5I-Setup.exe  (500MB-1GB)
```
✅ **Recommended for**: Enterprise internal distribution

### Standard Distribution
```
AI-System-DocAI-V5I-5I.2025.zip
├── AI-System-DocAI-V5I-Setup.exe
├── README.md
├── LICENSE
└── INSTALLATION_INSTRUCTIONS.md
```
✅ **Recommended for**: General distribution

### Complete Distribution
```
AI-System-DocAI-V5I-5I.2025-Complete.zip
├── AI-System-DocAI-V5I-Setup.exe
├── README.md
├── LICENSE
├── CHANGELOG.md
├── INSTALLATION_INSTRUCTIONS.md
├── QUICK_START_GUIDE.md
└── TROUBLESHOOTING.md
```
✅ **Recommended for**: Public distribution, comprehensive documentation

## 🛠️ Automated Build Script

Create `build_for_distribution.bat`:

```batch
@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo AI-System-DocAI V5I - Distribution Build Script
echo ============================================================
echo.

set VERSION=5I.2025
set RELEASE_NAME=AI-System-DocAI-V5I-%VERSION%-Release

echo [1] Cleaning previous builds...
if exist dist rd /s /q dist
if exist build rd /s /q build
if exist "%RELEASE_NAME%" rd /s /q "%RELEASE_NAME%"
if exist "%RELEASE_NAME%.zip" del /q "%RELEASE_NAME%.zip"
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
    echo     [ERROR] Verification failed!
    pause
    exit /b 1
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
mkdir "%RELEASE_NAME%"
copy dist\AI-System-DocAI-V5I-Setup.exe "%RELEASE_NAME%\" >nul
copy README.md "%RELEASE_NAME%\" >nul
if exist LICENSE copy LICENSE "%RELEASE_NAME%\" >nul
if exist docs\INSTALL.md copy docs\INSTALL.md "%RELEASE_NAME%\INSTALLATION_INSTRUCTIONS.md" >nul

echo     [OK] Release package created
echo.

echo [6] Creating ZIP archive...
powershell -Command "Compress-Archive -Path '%RELEASE_NAME%' -DestinationPath '%RELEASE_NAME%.zip' -Force"
if errorlevel 1 (
    echo     [WARNING] ZIP creation failed - manual compression may be needed
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
echo   - ZIP archive: %RELEASE_NAME%.zip
echo.
echo Ready for distribution!
echo.
pause
```

## 📋 Quick Start Distribution

### Immediate Distribution (If Already Built)

**Already have builds? Just create package:**

```batch
REM 1. Create release folder
mkdir Release

REM 2. Copy installer
copy dist\AI-System-DocAI-V5I-Setup.exe Release\

REM 3. Copy documentation
copy README.md Release\
if exist LICENSE copy LICENSE Release\

REM 4. Create ZIP
powershell Compress-Archive -Path Release -DestinationPath AI-System-DocAI-V5I-Release.zip
```

### Fresh Build & Distribution

```batch
REM 1. Run automated build script
build_for_distribution.bat

REM 2. Verify output
dir dist\AI-System-DocAI-V5I-Setup.exe
dir AI-System-DocAI-V5I-*.zip
```

## 🎯 Distribution Options

### Option 1: Single Installer File
**Best for**: Enterprise internal distribution

**Distribution**: Just share `AI-System-DocAI-V5I-Setup.exe`

**Pros**: Simple, single file, self-contained
**Cons**: Large file size

### Option 2: Installer + Documentation ZIP
**Best for**: General distribution

**Distribution**: Share ZIP containing installer + docs

**Pros**: Includes documentation, professional
**Cons**: Requires extraction

### Option 3: Portable Version
**Best for**: Users who don't want installation

**Distribution**: Share ZIP of extracted application

**Pros**: No installation needed
**Cons**: May need manual setup, larger package

## ✅ Pre-Distribution Final Check

Before sharing, verify:

1. **Installer Works**
   ```batch
   REM Test installer
   dist\AI-System-DocAI-V5I-Setup.exe /SILENT /DIR="C:\TestInstall"
   REM Verify installation works
   ```

2. **Application Runs**
   - Install on clean system
   - Launch application
   - Test basic functionality
   - Verify user data directories created

3. **Uninstaller Works**
   - Test uninstallation
   - Verify files removed
   - Test user data cleanup option

4. **File Integrity**
   - Installer size reasonable (500MB-1GB)
   - No corruption
   - All files included

## 📝 Next Steps

1. **Build the distribution package** using the script above
2. **Test on clean system** (VM recommended)
3. **Prepare release notes** if needed
4. **Upload to distribution channel**
5. **Share with users**

## 🚀 You're Ready!

Your application is ready for distribution. Follow the steps above to create your distribution package!

**Quick Command:**
```batch
REM Run automated build
build_for_distribution.bat

REM Result: AI-System-DocAI-V5I-5I.2025-Release.zip ready to distribute!
```


