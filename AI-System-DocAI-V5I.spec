# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AI-System-DocAI V5I
Optimized for Windows packaging with all dependencies included
"""

import sys
from pathlib import Path

block_cipher = None

# Get the source directory
src_dir = Path('src')

# Collect all Python files from src directory to include them as data
src_files = []
if src_dir.exists():
    for py_file in src_dir.rglob('*.py'):
        rel_path = py_file.relative_to(Path('.'))
        src_files.append((str(rel_path.parent), str(rel_path.parent)))

# Analysis phase - collects all dependencies
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),  # Include entire src directory
        ('assets', 'assets'),  # Include assets directory
    ] + (src_files if src_files else []),
    hiddenimports=[
        # PyQt6 core modules
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtPrintSupport',
        'PyQt6.sip',
        'sip',
        
        # Sentence Transformers and dependencies
        'sentence_transformers',
        'sentence_transformers.models',
        'sentence_transformers.util',
        'sentence_transformers.readers',
        'sentence_transformers.SentenceTransformer',
        
        # Transformers library
        'transformers',
        'transformers.models',
        'transformers.tokenization_utils',
        'transformers.configuration_utils',
        'transformers.modeling_utils',
        'transformers.AutoTokenizer',
        'transformers.AutoModelForCausalLM',
        
        # Tokenizers (C extension - critical!)
        'tokenizers',
        'tokenizers.implementations',
        'tokenizers.processors',
        'tokenizers.models',
        
        # PyTorch (CPU-only)
        'torch',
        'torch.nn',
        'torch.nn.functional',
        'torch.jit',
        'torch._C',
        'torch._C._nn',
        
        # FAISS
        'faiss',
        'faiss._swigfaiss',
        
        # Rank BM25
        'rank_bm25',
        'rank_bm25.BM25Okapi',
        
        # File processing libraries
        'pypdf',
        'pypdf.generic',
        'pypdf.errors',
        'fitz',  # PyMuPDF
        'docx2txt',
        'pptx',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.styles',
        'pandas',
        'pandas.io',
        'pandas.io.excel',
        'chardet',
        'chardet.universaldetector',
        
        # Configuration and utilities
        'toml',
        'psutil',
        'requests',
        
        # OpenAI
        'openai',
        'openai.api_resources',
        'openai.api_client',
        
        # Application modules (explicit imports)
        'ui',
        'llm',
        'reasoning',
        'config',
        'indexer',
        'retrieval',
        'embeddings',
        'loaders',
        'enterprise_logging',
        'index_manager',
        'streaming_reasoning',
        'streaming_reasoning_updated',
        'streaming_ui',
        'app_qt',
        'ingest',
        
        # Standard library modules that might be missed
        'json',
        'pathlib',
        'logging',
        'dataclasses',
        'typing',
        'collections',
        're',
        'time',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'test',
        'pytest',
        'unittest',
        'pydoc',
        'tkinter',  # Not using Tkinter
        'tornado',  # Not used
        'scipy',  # Not used (unless needed by transformers)
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Exclude unnecessary binaries to reduce size (optional)
# You can uncomment these if you want to reduce size further
# pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# For onefile mode (single executable)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI-System-DocAI-V5I',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Set to True if UPX is installed (may cause AV false positives)
    console=False,  # Set to True for debugging (shows console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app-icon.ico',
)

# For onedir mode (directory with executable + DLLs)
# This is MORE RELIABLE for large applications
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AI-System-DocAI-V5I',
)

# Uncomment below for onefile mode (single executable)
# Remove the COLLECT section above and use this instead:
# exe_onefile = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name='AI-System-DocAI-V5I',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=False,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon='assets/app-icon.ico',
# )

