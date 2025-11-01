# Inno Setup Installer Testing Guide

## Quick Test Checklist

### Pre-Build Verification

Run the verification script:
```batch
installer\verify_installer_setup.bat
```

This checks:
- ✅ PyInstaller build exists
- ✅ Main executable found
- ✅ src directory included
- ✅ Icon file exists
- ✅ Documentation files exist
- ✅ Inno Setup installed

### Build the Installer

```batch
iscc installer\windows_installer.iss
```

Or use Inno Setup Compiler GUI:
1. Open `installer/windows_installer.iss`
2. Build → Compile (F9)

### Testing the Installer

#### 1. Basic Installation Test

- [ ] Installer launches without errors
- [ ] Welcome page displays correctly
- [ ] License page shows (if LICENSE file exists)
- [ ] Installation directory defaults to Program Files
- [ ] Can change installation directory
- [ ] Progress bar works during installation
- [ ] Installation completes successfully
- [ ] No error messages appear

#### 2. File Installation Test

After installation, verify files exist:

**In Installation Directory** (`C:\Program Files\AI-System-DocAI\`):
- [ ] `AI-System-DocAI-V5I.exe` exists
- [ ] `src/` directory with all Python modules
- [ ] `assets/` directory with icon
- [ ] All required DLLs present
- [ ] `README.md` exists (if included)
- [ ] `LICENSE` exists (if included)

**In User Data Directory** (`%LOCALAPPDATA%\AI-System-DocAI\`):
- [ ] Directory created
- [ ] `faiss_index/` subdirectory created
- [ ] `logs/` subdirectory created
- [ ] `cache/` subdirectory created
- [ ] `models/` subdirectory created
- [ ] `logs/install.log` exists with installation details

#### 3. Shortcut Test

- [ ] Start Menu shortcut exists
  - Location: `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\AI-System-DocAI\`
- [ ] Desktop shortcut created (if option selected)
- [ ] Both shortcuts point to correct executable
- [ ] Icons display correctly

#### 4. Application Launch Test

- [ ] Application launches from Start Menu
- [ ] Application launches from Desktop shortcut
- [ ] Application launches from installation directory
- [ ] Application runs without errors
- [ ] GUI loads correctly
- [ ] No console errors (if console=False)

#### 5. Functionality Test

- [ ] Can select folders for indexing
- [ ] Can build index (creates files in user data dir)
- [ ] Can query indexed documents
- [ ] Logs are written to user data directory
- [ ] Configuration is saved to user directory

#### 6. Uninstallation Test

- [ ] Uninstaller appears in Control Panel
- [ ] Uninstaller launches correctly
- [ ] Prompts to delete user data
- [ ] Can choose to keep user data
- [ ] Can choose to delete user data
- [ ] Application files removed on uninstall
- [ ] Shortcuts removed
- [ ] User data removed (if option selected)
- [ ] User data kept (if option selected)

### Advanced Testing

#### Silent Installation Test

```batch
AI-System-DocAI-V5I-Setup.exe /SILENT
```

Verify:
- [ ] Installs without user interaction
- [ ] Installation completes
- [ ] Application works after silent install

#### Custom Directory Test

Install to custom location:
- [ ] Can select custom directory
- [ ] Files install to custom location
- [ ] Application works from custom location
- [ ] User data still goes to %LOCALAPPDATA%

#### Clean System Test

Test on a clean Windows system (VM recommended):
- [ ] Installer runs
- [ ] No missing dependencies
- [ ] Application works
- [ ] No Windows errors in Event Viewer

### Common Issues & Solutions

#### Issue: "PyInstaller build not found"

**Solution**: 
```batch
pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
```

#### Issue: Application doesn't launch after install

**Possible causes**:
1. Missing DLLs
2. Missing PyQt6 plugins
3. Path issues

**Solution**: 
- Rebuild with `--collect-all=PyQt6`
- Enable console mode in spec file to see errors
- Check `startup_errors.log` in user data directory

#### Issue: Installer size is very large

**Expected**: 500MB - 1GB (includes PyTorch, transformers)
This is normal for ML applications.

#### Issue: Icon not displaying

**Solution**: Ensure `assets/app-icon.ico` exists and is valid

### Testing Checklist Summary

**Installation**:
- ✅ Installer builds without errors
- ✅ Installer runs correctly
- ✅ Files installed correctly
- ✅ Shortcuts created
- ✅ User directories created

**Functionality**:
- ✅ Application launches
- ✅ All features work
- ✅ User data saved correctly
- ✅ No errors during operation

**Uninstallation**:
- ✅ Uninstaller works
- ✅ Files removed correctly
- ✅ User data handling works

## Automated Testing Script

Create `test_installer.bat`:

```batch
@echo off
echo Testing installer...
echo.

REM Build installer
echo [1] Building installer...
iscc installer\windows_installer.iss
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo [2] Installer built successfully!
echo Location: dist\AI-System-DocAI-V5I-Setup.exe
echo.
echo Please manually test the installer:
echo   1. Run the installer
echo   2. Complete installation
echo   3. Launch application
echo   4. Test functionality
echo   5. Uninstall and verify cleanup
echo.

pause
```

## Report Issues

If you find issues during testing:

1. Note the exact error message
2. Check `%LOCALAPPDATA%\AI-System-DocAI\logs\install.log`
3. Check `startup_errors.log` if app doesn't launch
4. Check Windows Event Viewer for system errors
5. Report with:
   - Windows version
   - Installation directory chosen
   - Exact error messages
   - Steps to reproduce

