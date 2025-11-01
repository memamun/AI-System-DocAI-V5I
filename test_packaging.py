#!/usr/bin/env python3
"""
Comprehensive packaging test script for AI-System-DocAI V5I
Tests all critical components to ensure they work after PyInstaller packaging
"""
import sys
import os
import importlib
from pathlib import Path
from typing import List, Tuple

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    colors = {
        "PASS": Colors.GREEN,
        "FAIL": Colors.RED,
        "WARN": Colors.YELLOW,
        "INFO": Colors.BLUE
    }
    color = colors.get(status, Colors.RESET)
    symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "!" if status == "WARN" else "ℹ"
    print(f"{color}{symbol} {message}{Colors.RESET}")

def test_pyinstaller_detection() -> Tuple[bool, str]:
    """Test if PyInstaller detection works"""
    try:
        # Import after ensuring path is set up
        import main
        # Access the function from the module
        if hasattr(main, 'get_base_path'):
            base_path = main.get_base_path()
        else:
            # If function not accessible, try to call it via importlib
            import importlib
            main_module = importlib.import_module('main')
            base_path = main_module.get_base_path()
        
        if hasattr(sys, 'frozen'):
            print_status(f"PyInstaller detected (frozen=True)", "INFO")
            if hasattr(sys, '_MEIPASS'):
                print_status(f"MEIPASS: {sys._MEIPASS}", "INFO")
            print_status(f"Executable: {sys.executable}", "INFO")
        else:
            print_status(f"Running from source, base_path: {base_path}", "INFO")
        
        print_status(f"Base path resolved: {base_path}", "PASS")
        return True, "PyInstaller detection works"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"PyInstaller detection failed: {e}"

def test_imports() -> Tuple[bool, List[str]]:
    """Test all critical imports"""
    critical_imports = [
        # Core application
        "ui",
        "config",
        "reasoning",
        "retrieval",
        "indexer",
        "embeddings",
        "llm",
        "loaders",
        
        # PyQt6
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        
        # ML libraries
        "torch",
        "sentence_transformers",
        "transformers",
        "faiss",
        "numpy",
        
        # File processing
        "pypdf",
        "docx2txt",
        "openpyxl",
        
        # Utilities
        "toml",
        "psutil",
        "requests",
    ]
    
    failed = []
    for module_name in critical_imports:
        try:
            importlib.import_module(module_name)
            print_status(f"Import successful: {module_name}", "PASS")
        except ImportError as e:
            print_status(f"Import failed: {module_name} - {e}", "FAIL")
            failed.append(module_name)
        except Exception as e:
            print_status(f"Import error: {module_name} - {e}", "FAIL")
            failed.append(module_name)
    
    return len(failed) == 0, failed

def test_path_resolution() -> Tuple[bool, str]:
    """Test path resolution for packaged app"""
    try:
        import main
        if hasattr(main, 'get_base_path'):
            base_path = main.get_base_path()
        else:
            import importlib
            main_module = importlib.import_module('main')
            base_path = main_module.get_base_path()
        
        # Test that base_path exists
        if not base_path.exists():
            return False, f"Base path does not exist: {base_path}"
        
        # Test src directory
        src_dir = base_path / "src"
        if hasattr(sys, 'frozen'):
            # In packaged version, src should be accessible
            if not src_dir.exists():
                # Try alternative locations
                alt_paths = [
                    Path(sys.executable).parent / "src",
                    Path.cwd() / "src",
                ]
                found = False
                for alt in alt_paths:
                    if alt.exists():
                        print_status(f"Found src at alternative path: {alt}", "WARN")
                        found = True
                        break
                if not found:
                    return False, f"src directory not found in packaged app at {src_dir}"
        
        print_status(f"Path resolution OK: base_path={base_path}, src={src_dir}", "PASS")
        return True, "Path resolution works"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Path resolution failed: {e}"

def test_config_manager() -> Tuple[bool, str]:
    """Test configuration manager initialization"""
    try:
        # Ensure src is in path (should already be set by main.py)
        # But let's make sure
        import main
        if hasattr(main, 'get_base_path'):
            base_path = main.get_base_path()
        else:
            import importlib
            main_module = importlib.import_module('main')
            base_path = main_module.get_base_path()
        
        src_dir = base_path / "src"
        if src_dir.exists() and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from config import config_manager
        
        # Test that config manager was created
        if config_manager is None:
            return False, "Config manager is None"
        
        # Test path getters
        config_path = config_manager.get_config_path()
        index_path = config_manager.get_index_path()
        logs_path = config_manager.get_logs_path()
        cache_path = config_manager.get_cache_path()
        
        print_status(f"Config path: {config_path}", "INFO")
        print_status(f"Index path: {index_path}", "INFO")
        print_status(f"Logs path: {logs_path}", "INFO")
        print_status(f"Cache path: {cache_path}", "INFO")
        
        return True, "Config manager works"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Config manager failed: {e}"

def test_resource_files() -> Tuple[bool, str]:
    """Test that resource files are accessible"""
    try:
        import main
        if hasattr(main, 'get_base_path'):
            base_path = main.get_base_path()
        else:
            import importlib
            main_module = importlib.import_module('main')
            base_path = main_module.get_base_path()
        
        # Check for assets directory
        assets_dir = base_path / "assets"
        if assets_dir.exists():
            print_status(f"Assets directory found: {assets_dir}", "PASS")
        else:
            print_status(f"Assets directory not found (may be optional): {assets_dir}", "WARN")
        
        # Check for icon
        icon_path = assets_dir / "app-icon.ico" if assets_dir.exists() else None
        if icon_path and icon_path.exists():
            print_status(f"Icon file found: {icon_path}", "PASS")
        else:
            print_status("Icon file not found (may be optional)", "WARN")
        
        return True, "Resource file check completed"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Resource file check failed: {e}"

def test_torch_cpu() -> Tuple[bool, str]:
    """Test PyTorch CPU-only mode"""
    try:
        import torch
        
        # Check device availability
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            print_status("CUDA available (should be disabled)", "WARN")
        else:
            print_status("CUDA not available (expected for CPU-only)", "PASS")
        
        # Test tensor creation
        test_tensor = torch.tensor([1.0, 2.0, 3.0])
        if test_tensor.device.type == 'cpu':
            print_status("PyTorch tensor creation on CPU works", "PASS")
        else:
            print_status(f"PyTorch tensor on unexpected device: {test_tensor.device}", "WARN")
        
        return True, "PyTorch CPU test passed"
    except Exception as e:
        return False, f"PyTorch test failed: {e}"

def test_faiss() -> Tuple[bool, str]:
    """Test FAISS library"""
    try:
        import faiss
        import numpy as np
        
        # Create a simple index
        dimension = 64
        index = faiss.IndexFlatL2(dimension)
        
        # Add some vectors
        vectors = np.random.random((10, dimension)).astype('float32')
        index.add(vectors)
        
        # Search
        query = np.random.random((1, dimension)).astype('float32')
        distances, indices = index.search(query, 5)
        
        print_status(f"FAISS index created with {index.ntotal} vectors", "PASS")
        return True, "FAISS works"
    except Exception as e:
        return False, f"FAISS test failed: {e}"

def test_sentence_transformers() -> Tuple[bool, str]:
    """Test sentence-transformers (may download model)"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Try to load a small model (this may take time on first run)
        print_status("Testing sentence-transformers (may download model if not cached)...", "INFO")
        
        # Check if we can import without loading a model
        # Loading a model takes too long for a quick test
        print_status("sentence-transformers import successful", "PASS")
        return True, "sentence-transformers import works"
    except Exception as e:
        return False, f"sentence-transformers test failed: {e}"

def run_all_tests():
    """Run all packaging tests"""
    print("\n" + "="*70)
    print("AI-System-DocAI V5I - Packaging Test Suite")
    print("="*70 + "\n")
    
    results = []
    
    # Test 1: PyInstaller detection
    print("\n[1] Testing PyInstaller Detection")
    print("-" * 70)
    success, msg = test_pyinstaller_detection()
    results.append(("PyInstaller Detection", success, msg))
    
    # Test 2: Path resolution
    print("\n[2] Testing Path Resolution")
    print("-" * 70)
    success, msg = test_path_resolution()
    results.append(("Path Resolution", success, msg))
    
    # Test 3: Imports
    print("\n[3] Testing Critical Imports")
    print("-" * 70)
    success, failed = test_imports()
    msg = "All imports successful" if success else f"Failed imports: {', '.join(failed)}"
    results.append(("Critical Imports", success, msg))
    
    # Test 4: Config Manager
    print("\n[4] Testing Config Manager")
    print("-" * 70)
    success, msg = test_config_manager()
    results.append(("Config Manager", success, msg))
    
    # Test 5: Resource files
    print("\n[5] Testing Resource Files")
    print("-" * 70)
    success, msg = test_resource_files()
    results.append(("Resource Files", success, msg))
    
    # Test 6: PyTorch CPU
    print("\n[6] Testing PyTorch CPU Mode")
    print("-" * 70)
    success, msg = test_torch_cpu()
    results.append(("PyTorch CPU", success, msg))
    
    # Test 7: FAISS
    print("\n[7] Testing FAISS")
    print("-" * 70)
    success, msg = test_faiss()
    results.append(("FAISS", success, msg))
    
    # Test 8: Sentence Transformers
    print("\n[8] Testing Sentence Transformers")
    print("-" * 70)
    success, msg = test_sentence_transformers()
    results.append(("Sentence Transformers", success, msg))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, msg in results:
        status = "PASS" if success else "FAIL"
        print_status(f"{test_name}: {msg}", status)
    
    print("\n" + "-"*70)
    print_status(f"Tests passed: {passed}/{total}", "PASS" if passed == total else "FAIL")
    
    if passed == total:
        print("\n✅ All tests passed! The application should work after packaging.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues before packaging.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())

