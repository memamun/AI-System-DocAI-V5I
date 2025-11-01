# PyInstaller Packaging Checklist & Requirements

## Overview
This document outlines all required packages, hidden imports, and potential issues for packaging AI-System-DocAI V5I with PyInstaller.

---

## 1. Required Packages (from pyproject.toml)

### Core Dependencies
- ✅ `PyQt6>=6.6.0` - GUI framework
- ✅ `faiss-cpu>=1.7.4` - Vector similarity search
- ✅ `sentence-transformers>=2.2.2` - Embedding models
- ✅ `rank-bm25>=0.2.2` - Sparse retrieval
- ✅ `numpy>=1.24.0,<2.0.0` - Numerical operations
- ✅ `torch>=2.0.0,<2.3.0` - Deep learning framework (CPU-only)
- ✅ `transformers>=4.30.0` - HuggingFace transformers
- ✅ `pypdf>=3.15.0` - PDF processing
- ✅ `pymupdf>=1.22.5` - PDF processing (alternative)
- ✅ `docx2txt>=0.8` - DOCX processing
- ✅ `python-pptx>=0.6.21` - PPTX processing
- ✅ `pandas>=2.0.0` - Data processing
- ✅ `openpyxl>=3.1.0` - Excel processing
- ✅ `chardet>=5.1.0` - Character encoding detection
- ✅ `toml>=0.10.2` - Configuration file parsing
- ✅ `psutil>=5.9.5` - System information
- ✅ `requests>=2.31.0` - HTTP requests
- ✅ `openai>=1.0.0` - OpenAI API client

### LLM Backends
- `openai>=1.0.0` - OpenAI API client
- Ollama - Local server (no package needed)
- HuggingFace - Local models (included via transformers)

---

## 2. Hidden Imports (Must be explicitly included)

These modules are imported dynamically or through package internals and PyInstaller may miss them:

```python
# PyQt6 hidden imports
--hidden-import=PyQt6.QtCore
--hidden-import=PyQt6.QtGui
--hidden-import=PyQt6.QtWidgets
--hidden-import=sip

# Sentence Transformers hidden imports
--hidden-import=sentence_transformers
--hidden-import=sentence_transformers.models
--hidden-import=sentence_transformers.util
--hidden-import=sentence_transformers.readers

# Transformers hidden imports
--hidden-import=transformers
--hidden-import=transformers.models
--hidden-import=transformers.tokenization_utils
--hidden-import=transformers.configuration_utils

# HuggingFace tokenizers (C extension)
--hidden-import=tokenizers
--hidden-import=tokenizers.processors

# PyTorch hidden imports
--hidden-import=torch
--hidden-import=torch.nn
--hidden-import=torch.nn.functional
--hidden-import=torch.jit
--hidden-import=torch.onnx

# FAISS hidden imports
--hidden-import=faiss
--hidden-import=faiss._swigfaiss

# File processing hidden imports
--hidden-import=pypdf
--hidden-import=pypdf.generic
--hidden-import=fitz  # PyMuPDF
--hidden-import=docx2txt
--hidden-import=pptx
--hidden-import=openpyxl
--hidden-import=pandas
--hidden-import=chardet

# Configuration
--hidden-import=toml
--hidden-import=psutil

# LLM backends
--hidden-import=openai
--hidden-import=openai.api_resources
```

---

## 3. Data Files & Resources to Include

### Sentence Transformers Models
Models are downloaded from HuggingFace at runtime. You have two options:

**Option A: Include model files (LARGE - ~100MB+)**
```python
--add-data="C:/Users/username/.cache/huggingface/transformers/*;huggingface/transformers"
--add-data="C:/Users/username/.cache/huggingface/hub/*;huggingface/hub"
```

**Option B: Let models download at runtime (RECOMMENDED)**
- Models will download to user's cache directory on first use
- No need to bundle them (reduces package size significantly)

### Configuration Files
- `pyproject.toml` - Package metadata (if needed)
- Default configs are generated programmatically

### No Static Resources Needed
- No icons, images, or other static files detected

---

## 4. Known PyInstaller Issues & Solutions

### Issue 1: PyQt6 DLL Loading
**Problem:** PyQt6 plugins may not be found
**Solution:**
```python
--collect-all=PyQt6
# OR explicitly:
--collect-submodules=PyQt6
```

### Issue 2: PyTorch Model Loading
**Problem:** PyTorch models may fail to load in frozen executable
**Solution:**
```python
--hidden-import=torch._C
--hidden-import=torch._C._nn
```

### Issue 3: FAISS Binary Compatibility
**Problem:** FAISS may fail on some systems due to architecture mismatch
**Solution:**
- Use `faiss-cpu` (already in requirements)
- Test on target architecture
- Consider including: `--collect-all=faiss`

### Issue 4: Sentence Transformers Tokenizers
**Problem:** Tokenizers may fail to load (C extension)
**Solution:**
```python
--hidden-import=tokenizers
--hidden-import=tokenizers.implementations
--hidden-import=tokenizers.processors
```

### Issue 5: Dynamic Imports in LLM Modules
**Problem:** LLM backends are conditionally imported
**Solution:**
- Either include all optional backends as hidden imports
- OR use `--exclude-module` for unused backends to reduce size

### Issue 6: Windows DLL Dependencies
**Problem:** Missing system DLLs (MSVCP140.dll, etc.)
**Solution:**
```python
--collect-all=torch
--collect-all=sentence_transformers
```

---

## 5. Recommended PyInstaller Command

### Windows (One-File Executable)
```bash
pyinstaller --name="AI-System-DocAI-V5I" \
  --onefile \
  --windowed \
  --icon=NONE \
  --add-data="src;src" \
  --hidden-import=PyQt6.QtCore \
  --hidden-import=PyQt6.QtGui \
  --hidden-import=PyQt6.QtWidgets \
  --hidden-import=sip \
  --hidden-import=sentence_transformers \
  --hidden-import=transformers \
  --hidden-import=tokenizers \
  --hidden-import=torch \
  --hidden-import=torch._C \
  --hidden-import=faiss \
  --hidden-import=pypdf \
  --hidden-import=fitz \
  --hidden-import=docx2txt \
  --hidden-import=pptx \
  --hidden-import=openpyxl \
  --hidden-import=pandas \
  --hidden-import=chardet \
  --hidden-import=toml \
  --hidden-import=psutil \
  --hidden-import=openai \
  --collect-all=PyQt6 \
  --collect-all=torch \
  --exclude-module=matplotlib \
  --exclude-module=IPython \
  --exclude-module=jupyter \
  main.py
```

### Windows (Directory Mode - More Reliable for Large Apps)
```bash
pyinstaller --name="AI-System-DocAI-V5I" \
  --onedir \
  --windowed \
  --icon=NONE \
  --add-data="src;src" \
  --hidden-import=PyQt6.QtCore \
  --hidden-import=PyQt6.QtGui \
  --hidden-import=PyQt6.QtWidgets \
  --hidden-import=sip \
  --hidden-import=sentence_transformers \
  --hidden-import=transformers \
  --hidden-import=tokenizers \
  --hidden-import=torch \
  --hidden-import=faiss \
  --collect-all=PyQt6 \
  --exclude-module=matplotlib \
  --exclude-module=IPython \
  main.py
```

---

## 6. Potential Runtime Issues After Packaging

### Issue: Sentence Transformers Model Download
**What happens:** First run downloads model (~90MB) from HuggingFace
**Impact:** Slower first startup, requires internet
**Solution:** Document this in user guide

### Issue: Config File Creation
**What happens:** Config created in `%LOCALAPPDATA%\AI-System-DocAI\config.toml`
**Impact:** None - this is expected behavior
**Solution:** Already handled in code

### Issue: FAISS Index Files
**What happens:** Index files created in local directory
**Impact:** None - this is expected
**Solution:** Already handled in code

### Issue: Large Binary Size
**Expected size:** 500MB - 1GB (due to PyTorch, transformers, etc.)
**Impact:** Large download/install size
**Solution:** 
- Consider using UPX compression (may cause AV false positives)
- Consider splitting into installer

### Issue: Antivirus False Positives
**Why:** Large Python executables often flagged
**Solution:**
- Code sign the executable (requires certificate)
- Submit to antivirus vendors for whitelisting
- Provide checksums for verification

---

## 7. Testing Checklist

After packaging, test:

- [ ] Application starts without errors
- [ ] GUI loads correctly
- [ ] File indexing works (PDF, DOCX, PPTX, XLSX)
- [ ] Embedding model loads (may download on first run)
- [ ] FAISS index creation works
- [ ] Document query/retrieval works
- [ ] LLM backends work (test each one)
- [ ] Configuration saves/loads correctly
- [ ] Logging works
- [ ] No console errors on startup
- [ ] File dialogs work
- [ ] Status messages display correctly

---

## 8. Size Optimization Tips

### Exclude Unused Modules
```python
--exclude-module=matplotlib
--exclude-module=IPython
--exclude-module=jupyter
--exclude-module=notebook
--exclude-module=pytest
--exclude-module=test
```

### Use Directory Mode
- Directory mode (`--onedir`) is more reliable than one-file
- Faster startup time
- Easier to debug

### Compress with UPX (Optional)
```bash
--upx-dir=C:/path/to/upx
```
**Warning:** May trigger antivirus

---

## 9. Build Script Example

Create `build_exe.bat`:
```batch
@echo off
echo Building AI-System-DocAI V5I executable...

pyinstaller --name="AI-System-DocAI-V5I" ^
  --onedir ^
  --windowed ^
  --icon=NONE ^
  --add-data="src;src" ^
  --hidden-import=PyQt6.QtCore ^
  --hidden-import=PyQt6.QtGui ^
  --hidden-import=PyQt6.QtWidgets ^
  --hidden-import=sip ^
  --hidden-import=sentence_transformers ^
  --hidden-import=transformers ^
  --hidden-import=tokenizers ^
  --hidden-import=torch ^
  --hidden-import=faiss ^
  --collect-all=PyQt6 ^
  --exclude-module=matplotlib ^
  --exclude-module=IPython ^
  main.py

echo.
echo Build complete! Check dist/ directory.
pause
```

---

## 10. Critical Notes

1. **First Run Download:** Users will need internet on first run for model download
2. **Large Size:** Expect 500MB-1GB executable
3. **CPU-Only:** Application is CPU-only (no CUDA), which simplifies packaging
4. **Windows DLLs:** May need Visual C++ Redistributables on target systems
5. **Testing:** Must test on clean Windows VM to ensure all dependencies included

---

## 11. Alternative: Create PyInstaller Spec File

For more control, create `AI-System-DocAI-V5I.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sip',
        'sentence_transformers',
        'transformers',
        'tokenizers',
        'torch',
        'faiss',
        'pypdf',
        'fitz',
        'docx2txt',
        'pptx',
        'openpyxl',
        'pandas',
        'chardet',
        'toml',
        'psutil',
        'openai',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'IPython', 'jupyter', 'test', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI-System-DocAI-V5I',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For onefile mode, use the above EXE
# For onedir mode, use below:
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='AI-System-DocAI-V5I',
# )
```

Build with:
```bash
pyinstaller AI-System-DocAI-V5I.spec
```

---

## Summary

**Critical Requirements:**
1. All hidden imports listed above
2. PyQt6 collection (`--collect-all=PyQt6`)
3. Source directory inclusion (`--add-data="src;src"`)
4. Directory mode recommended over one-file for reliability
5. Test thoroughly on clean Windows system

**Expected Issues:**
1. Large file size (500MB-1GB) - normal for ML apps
2. First-run model download - document for users
3. Possible AV false positives - consider code signing
4. Long build time (5-15 minutes) - normal

**Success Criteria:**
- Executable runs without import errors
- All features work as expected
- No console errors on startup
- Models download and load correctly

