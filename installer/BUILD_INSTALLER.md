# Building the Windows Installer

## Prerequisites

1. **Inno Setup** installed (download from: https://jrsoftware.org/isdl.php)
   - Recommended version: 6.2.0 or later
   - Make sure to install Inno Setup Compiler

2. **PyInstaller build completed**
   - Build the application first: `pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec`
   - Build output should be in: `dist/AI-System-DocAI-V5I/`

## Build Steps

### Step 1: Build PyInstaller Application

```bash
# From project root directory
pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
```

This creates:
- `dist/AI-System-DocAI-V5I/` directory
- Contains: `AI-System-DocAI-V5I.exe`, DLLs, `src/`, `assets/`, etc.

### Step 2: Verify Build Structure

Check that the following exist:
- ✅ `dist/AI-System-DocAI-V5I/AI-System-DocAI-V5I.exe`
- ✅ `dist/AI-System-DocAI-V5I/src/` directory
- ✅ `dist/AI-System-DocAI-V5I/assets/` directory (with app-icon.ico)
- ✅ `assets/app-icon.ico` (for installer icon)

### Step 3: Build the Installer

#### Option A: Using Inno Setup Compiler GUI

1. Open Inno Setup Compiler
2. File → Open
3. Select `installer/windows_installer.iss`
4. Build → Compile (or press F9)
5. Wait for compilation to complete
6. Installer will be in: `dist/AI-System-DocAI-V5I-Setup.exe`

#### Option B: Using Command Line

```bash
# If Inno Setup is in PATH:
iscc installer/windows_installer.iss

# Or with full path:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer/windows_installer.iss
```

### Step 4: Test the Installer

1. **Run the installer** (`dist/AI-System-DocAI-V5I-Setup.exe`)
2. **Verify installation**:
   - Default location: `C:\Program Files\AI-System-DocAI\`
   - Check that all files are installed
   - Verify Start Menu shortcut exists
3. **Launch the application**:
   - From Start Menu
   - From Desktop (if option was selected)
   - Directly from installation directory
4. **Verify user data directories**:
   - Check: `%LOCALAPPDATA%\AI-System-DocAI\`
   - Should contain: `faiss_index\`, `logs\`, `cache\`, `models\`

### Step 5: Test Uninstallation

1. **Uninstall from Control Panel**
2. **Verify**:
   - Application files are removed
   - Start Menu shortcuts removed
   - Option to keep/delete user data

## Installer Features

### ✅ What the Installer Does

1. **Copies all files** from PyInstaller build
2. **Creates Start Menu shortcuts**
3. **Optionally creates Desktop shortcut**
4. **Creates user data directories** in `%LOCALAPPDATA%`
5. **Registers uninstaller** in Windows
6. **Validates** that PyInstaller build exists before installing

### 📁 Installation Structure

```
C:\Program Files\AI-System-DocAI\
├── AI-System-DocAI-V5I.exe  (main executable)
├── src\                      (application modules)
├── assets\                   (icons and resources)
├── *.dll                     (all required DLLs)
├── README.md
└── LICENSE

%LOCALAPPDATA%\AI-System-DocAI\
├── faiss_index\              (document indexes - created by app)
├── logs\                     (application logs - created by app)
├── cache\                    (model cache - created by app)
├── models\                   (downloaded models - created by app)
└── config.toml              (user configuration - created by app)
```

### 🔍 Validation Checks

The installer script includes validation:

1. **Pre-installation check**: Verifies PyInstaller build exists
2. **File existence checks**: Ensures all required files are present
3. **Error messages**: Clear error messages if prerequisites are missing

## Troubleshooting

### Error: "PyInstaller build not found"

**Solution**: Build the application first:
```bash
pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
```

### Error: "Icon file not found"

**Solution**: Ensure `assets/app-icon.ico` exists in the project root.

### Error: "Main executable not found"

**Solution**: 
- Verify the PyInstaller build completed successfully
- Check `dist/AI-System-DocAI-V5I/AI-System-DocAI-V5I.exe` exists
- Rebuild if necessary

### Installer builds but application doesn't run

**Possible causes**:
1. Missing DLLs - Check PyInstaller collected all dependencies
2. Missing PyQt6 plugins - Rebuild with `--collect-all=PyQt6`
3. Path issues - Check that `src/` directory is included

**Solution**: Rebuild with console mode enabled to see errors:
```python
# In AI-System-DocAI-V5I.spec, change:
console=True,  # Was False
```

### Installer is too large

**Expected size**: 500MB - 1GB (includes PyTorch, transformers, etc.)
This is normal for ML applications.

## Advanced Configuration

### Custom Installation Directory

Users can choose custom directory during installation.

### Silent Installation

To install silently:
```bash
AI-System-DocAI-V5I-Setup.exe /SILENT
```

To install with custom directory:
```bash
AI-System-DocAI-V5I-Setup.exe /SILENT /DIR="C:\Custom\Path"
```

### Unattended Installation

```bash
AI-System-DocAI-V5I-Setup.exe /VERYSILENT /NORESTART
```

## Build Automation

### Batch Script for Complete Build

Create `build_all.bat`:

```batch
@echo off
echo Building AI-System-DocAI V5I...
echo.

echo Step 1: Building with PyInstaller...
pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
if errorlevel 1 (
    echo PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Building installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer/windows_installer.iss
if errorlevel 1 (
    echo Installer build failed!
    pause
    exit /b 1
)

echo.
echo Build complete! Installer: dist\AI-System-DocAI-V5I-Setup.exe
pause
```

## Verification Checklist

After building installer, verify:

- [ ] Installer builds without errors
- [ ] Installer runs and shows wizard
- [ ] Installation completes successfully
- [ ] Application launches from Start Menu
- [ ] Application launches from Desktop (if option selected)
- [ ] Application runs correctly
- [ ] User data directories created in `%LOCALAPPDATA%`
- [ ] Uninstaller works correctly
- [ ] No errors in Windows Event Viewer

## Distribution

The installer (`AI-System-DocAI-V5I-Setup.exe`) can be distributed:
- Via download link
- On USB drives
- Through software deployment systems
- Internal enterprise distribution

**Note**: The installer is a standalone executable - no additional files needed for distribution.

