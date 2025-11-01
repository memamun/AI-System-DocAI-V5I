# Quick PyInstaller Build Guide

## 🚀 Fastest Way to Build

### Option 1: Use the Batch Script (Easiest)
```bash
build_exe.bat
```

### Option 2: Use the Spec File
```bash
pyinstaller AI-System-DocAI-V5I.spec
```

### Option 3: Command Line
```bash
pyinstaller --onedir --windowed --name="AI-System-DocAI-V5I" ^
  --hidden-import=sentence_transformers --hidden-import=tokenizers ^
  --hidden-import=torch --hidden-import=torch._C --hidden-import=faiss ^
  --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets ^
  --collect-all=PyQt6 --add-data="src;src" main.py
```

---

## ⚡ Critical Hidden Imports (Don't Forget!)

These 5 are absolutely essential:
1. `sentence_transformers`
2. `tokenizers` 
3. `torch` + `torch._C`
4. `faiss`
5. `PyQt6.QtCore` + `PyQt6.QtGui` + `PyQt6.QtWidgets`

---

## 📦 Expected Results

- **Build Time:** 5-15 minutes
- **Executable Size:** 500MB - 1GB
- **Location:** `dist/AI-System-DocAI-V5I/` (directory mode)

---

## ✅ Quick Test Checklist

After building, test:
1. [ ] App starts without errors
2. [ ] GUI appears
3. [ ] Can index a PDF
4. [ ] Can query documents

---

## 🐛 Common Issues

### "ModuleNotFoundError: No module named 'X'"
→ Add `--hidden-import=X` to the command

### "DLL load failed"
→ Use `--collect-all=PyQt6` and `--collect-all=torch`

### App crashes on startup
→ Build with `--console=True` first to see errors

### Large file size warning
→ This is normal for ML apps (500MB-1GB expected)

---

## 📚 Full Documentation

- **Detailed Checklist:** `PYINSTALLER_PACKAGING_CHECKLIST.md`
- **Summary:** `PACKAGING_SUMMARY.md`
- **Spec File:** `AI-System-DocAI-V5I.spec`

---

**That's it!** The spec file has everything pre-configured. Just run `build_exe.bat` and you're good to go! 🎉

