# Build Instructions for AI-System-DocAI V5I

## Prerequisites

1. **Python 3.8+** installed
2. **PyInstaller** installed: `pip install pyinstaller`
3. **All dependencies** installed in your environment

## Building with PyInstaller

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build the Application

#### Option A: Using the Spec File (Recommended)
```bash
pyinstaller AI-System-DocAI-V5I.spec
```

#### Option B: Command Line (Alternative)
```bash
pyinstaller --name="AI-System-DocAI-V5I" \
  --onedir \
  --windowed \
  --icon=assets/app-icon.ico \
  --add-data="src;src" \
  --add-data="assets;assets" \
  --collect-all=PyQt6 \
  --hidden-import=PyQt6.QtCore \
  --hidden-import=PyQt6.QtGui \
  --hidden-import=PyQt6.QtWidgets \
  --hidden-import=sentence_transformers \
  --hidden-import=transformers \
  --hidden-import=tokenizers \
  --hidden-import=torch \
  --hidden-import=faiss \
  --exclude-module=matplotlib \
  --exclude-module=IPython \
  --exclude-module=jupyter \
  main.py
```

### Step 3: Test the Build

After building, test the executable:

```bash
# Navigate to the build output
cd dist/AI-System-DocAI-V5I

# Run the executable
./AI-System-DocAI-V5I  # Linux/macOS
# or
AI-System-DocAI-V5I.exe  # Windows
```

### Step 4: Create Installer (Windows)

If using Inno Setup:

```bash
# Compile the installer
iscc installer/windows_installer.iss
```

The installer will be created in `dist/AI-System-DocAI-V5I-Setup.exe`

## Important Notes

### Path Handling
- **Source mode**: Data files (index, logs, cache) are created relative to the application directory
- **Packaged mode**: Data files are created in user directories:
  - Windows: `%LOCALAPPDATA%\AI-System-DocAI\`
  - Linux: `~/.local/share/AI-System-DocAI/` and `~/.cache/AI-System-DocAI/`

### Debugging Build Issues

If the packaged application doesn't work:

1. **Enable Console Mode** (in spec file):
   ```python
   console=True,  # Change from False to True
   ```

2. **Check Error Logs**:
   - Windows: `%LOCALAPPDATA%\AI-System-DocAI\logs\startup_errors.log`
   - Linux: `~/.local/share/AI-System-DocAI/logs/startup_errors.log`

3. **Test Imports**:
   Run `python test_packaging.py` before building to verify all dependencies

### Common Issues

#### Missing PyQt6 Plugins
If you get "No Qt platform plugin" errors, add to command line:
```bash
--collect-all=PyQt6
```

#### Missing Hidden Imports
If you get import errors, add missing modules to `hiddenimports` in the spec file.

#### Large File Size
The executable will be 500MB-1GB due to PyTorch and transformers libraries. This is normal.

## Build Output

After successful build:
- **Location**: `dist/AI-System-DocAI-V5I/`
- **Contents**:
  - `AI-System-DocAI-V5I.exe` (Windows) or `AI-System-DocAI-V5I` (Linux)
  - `src/` directory with all application modules
  - `assets/` directory with icons
  - All required DLLs and dependencies

## Verification Checklist

After building, verify:
- [ ] Application starts without errors
- [ ] GUI loads correctly
- [ ] Can select folders for indexing
- [ ] Can build index
- [ ] Can query indexed documents
- [ ] LLM backends work (if configured)
- [ ] Logs are created in user directory
- [ ] No console errors (if console=False)

