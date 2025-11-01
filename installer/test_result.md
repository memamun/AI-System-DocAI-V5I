(.venv) PS C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I> python test_packaging.py

======================================================================
AI-System-DocAI V5I - Packaging Test Suite
======================================================================


[1] Testing PyInstaller Detection
----------------------------------------------------------------------
ℹ Running from source, base_path: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I
✓ Base path resolved: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I

[2] Testing Path Resolution
----------------------------------------------------------------------
✓ Path resolution OK: base_path=C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I, src=C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\src

[3] Testing Critical Imports
----------------------------------------------------------------------
00:46:41 | INFO | ================================================================================
00:46:41 | INFO | AI-System-DocAI V5I.2025 Starting Up
00:46:41 | INFO | ================================================================================
00:46:41 | INFO | SYSTEM INFORMATION:
00:46:41 | INFO |   os: Windows
00:46:41 | INFO |   os_version: 10.0.26200
00:46:41 | INFO |   architecture: 64bit
00:46:41 | INFO |   processor: Intel64 Family 6 Model 78 Stepping 3, GenuineIntel
00:46:41 | INFO |   python_version: 3.12.10
00:46:41 | INFO |   Total RAM: 7.9 GB
00:46:41 | INFO |   Available RAM: 1.6 GB
00:46:41 | INFO |   RAM Usage: 79.7%
00:46:41 | INFO |   CPU Cores: 2 physical, 4 logical
00:46:42 | INFO |   CPU Usage: 19.1%
00:46:42 | INFO | CONFIGURATION:
00:46:42 | INFO |   Config Path: C:\Users\aamam\AppData\Local\AI-System-DocAI\config.toml
00:46:42 | INFO |   Index Dir: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\faiss_index
00:46:42 | INFO |   Logs Dir: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\logs
00:46:42 | INFO |   LLM Backend: ollama
00:46:42 | INFO |   Embedding Model: sentence-transformers/all-MiniLM-L6-v2
00:46:42 | INFO |   Device: CPU (forced)
00:46:42 | INFO | SECURITY SETTINGS:
00:46:42 | INFO |   Internal LAN Mode: True
00:46:42 | INFO |   Audit Logging: True
00:46:42 | INFO | ENTERPRISE FEATURES:
00:46:42 | INFO |   Multi-User: False
00:46:42 | INFO |   Audit Logging: True
00:46:42 | INFO |   Backup Enabled: True
00:46:42 | INFO | ================================================================================
✓ Import successful: ui
✓ Import successful: config
✓ Import successful: reasoning
✓ Import successful: retrieval
✓ Import successful: indexer
✓ Import successful: embeddings
✓ Import successful: llm
✓ Import successful: loaders
✓ Import successful: PyQt6.QtCore
✓ Import successful: PyQt6.QtGui
✓ Import successful: PyQt6.QtWidgets
✓ Import successful: torch
✓ Import successful: sentence_transformers
✓ Import successful: transformers
✓ Import successful: faiss
✓ Import successful: numpy
✓ Import successful: pypdf
✓ Import successful: docx2txt
✓ Import successful: openpyxl
✓ Import successful: toml
✓ Import successful: psutil
✓ Import successful: requests

[4] Testing Config Manager
----------------------------------------------------------------------
ℹ Config path: C:\Users\aamam\AppData\Local\AI-System-DocAI\config.toml
ℹ Index path: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\faiss_index
ℹ Logs path: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\logs
ℹ Cache path: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\cache

[5] Testing Resource Files
----------------------------------------------------------------------
✓ Assets directory found: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\assets
✓ Icon file found: C:\Users\aamam\projects\sheldon\AI-System-DocAI-V5I\assets\app-icon.ico

[6] Testing PyTorch CPU Mode
----------------------------------------------------------------------
✓ CUDA not available (expected for CPU-only)
✓ PyTorch tensor creation on CPU works

[7] Testing FAISS
----------------------------------------------------------------------
✓ FAISS index created with 10 vectors

[8] Testing Sentence Transformers
----------------------------------------------------------------------
ℹ Testing sentence-transformers (may download model if not cached)...
✓ sentence-transformers import successful

======================================================================
TEST SUMMARY
======================================================================

✓ PyInstaller Detection: PyInstaller detection works
✓ Path Resolution: Path resolution works
✓ Critical Imports: All imports successful
✓ Config Manager: Config manager works
✓ Resource Files: Resource file check completed
✓ PyTorch CPU: PyTorch CPU test passed
✓ FAISS: FAISS works
✓ Sentence Transformers: sentence-transformers import works

----------------------------------------------------------------------
✓ Tests passed: 8/8

✅ All tests passed! The application should work after packaging.