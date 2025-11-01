#!/usr/bin/env python3
"""
AI-System-DocAI V5I - Enterprise Edition
Main application entry point
"""
import sys
import os
import platform
from pathlib import Path

def ensure_venv_used():
    """Ensure we're using .venv if it exists (only when running from source)"""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller - venv is not used (dependencies are bundled)
        return
    
    # Running from source - check for .venv and use it if available
    base_path = Path(__file__).parent
    venv_path = base_path / ".venv"
    
    if venv_path.exists():
        # Determine Python executable in venv based on OS
        if platform.system() == "Windows":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"
        
        if venv_python.exists():
            # Check if we're already using the venv
            current_python = Path(sys.executable).resolve()
            venv_python_resolved = venv_python.resolve()
            
            if current_python != venv_python_resolved:
                # Not using venv - warn user but don't fail
                # The launcher should handle this, but direct execution might miss it
                print(f"⚠️  Warning: Not using .venv. Please use launcher.py or activate .venv manually.")
                print(f"   Current Python: {current_python}")
                print(f"   Venv Python: {venv_python_resolved}")

# PyInstaller compatibility: detect if running from packaged executable
def get_base_path():
    """Get the base path whether running from source or PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller
        # In onedir mode: executable is in a folder, data files are in the same folder as the executable
        # In onefile mode: sys._MEIPASS is the temp directory, but files are also extracted to executable's dir
        if hasattr(sys, '_MEIPASS'):
            # During boot, try both locations
            # First try the executable's directory (onedir mode, or onefile after extraction)
            exe_dir = Path(sys.executable).parent
            # Check if src exists in executable's directory (typical for onedir)
            if (exe_dir / "src").exists():
                return exe_dir
            # Otherwise, try MEIPASS (onefile mode during boot)
            meipass_dir = Path(sys._MEIPASS)
            if (meipass_dir / "src").exists():
                return meipass_dir
            # Default to executable directory
            return exe_dir
        else:
            # No MEIPASS, use executable directory
            return Path(sys.executable).parent
    else:
        # Running from source
        return Path(__file__).parent

# Add src directory to Python path
base_path = get_base_path()
src_dir = base_path / "src"

# Check if src exists (should always exist in packaged version, or in source)
if src_dir.exists() and src_dir.is_dir():
    sys.path.insert(0, str(src_dir))
else:
    # Fallback: try to find src relative to current working directory
    # This handles edge cases where __file__ might not work as expected
    cwd_src = Path.cwd() / "src"
    if cwd_src.exists() and cwd_src.is_dir():
        sys.path.insert(0, str(cwd_src))
    else:
        # Last resort: if we're in a packaged app, src should be in the same directory
        # PyInstaller puts data files in the same directory as the executable (onedir mode)
        potential_src = Path(sys.executable).parent / "src" if hasattr(sys, 'frozen') else None
        if potential_src and potential_src.exists():
            sys.path.insert(0, str(potential_src))

# Ensure .venv is used when running from source
ensure_venv_used()

# Force CPU-only mode globally
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

def main():
    """Main entry point"""
    try:
        # Import UI after path setup
        from ui import main as ui_main
        
        # Run the application
        return ui_main()
        
    except ImportError as e:
        error_msg = str(e)
        is_packaged = getattr(sys, 'frozen', False)
        
        print(f"Import Error: {error_msg}")
        if is_packaged:
            print("\nThis is a packaged application. The import error suggests:")
            print("  1. Missing dependency in PyInstaller build")
            print("  2. Corrupted installation")
            print("\nPlease contact support or reinstall the application.")
            print(f"\nFor debugging, check if console mode is enabled.")
        else:
            print("\nPlease ensure all dependencies are installed:")
            print("  pip install -r requirements.txt")
            print("  Or use: launcher.py (creates .venv automatically)")
        
        # Try to write error to log if possible
        try:
            base_path = get_base_path()
            logs_dir = base_path / "logs"
            logs_dir.mkdir(exist_ok=True)
            error_log = logs_dir / "startup_errors.log"
            with open(error_log, 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"\n[{datetime.now()}] Import Error: {error_msg}\n")
                import traceback
                f.write(traceback.format_exc())
        except:
            pass  # If we can't log, continue anyway
        
        return 1
    except Exception as e:
        error_msg = str(e)
        is_packaged = getattr(sys, 'frozen', False)
        
        print(f"Error starting application: {error_msg}")
        import traceback
        traceback.print_exc()
        
        if is_packaged:
            print("\nThis is a packaged application. Error details have been logged.")
            try:
                base_path = get_base_path()
                logs_dir = base_path / "logs"
                logs_dir.mkdir(exist_ok=True)
                error_log = logs_dir / "startup_errors.log"
                with open(error_log, 'a', encoding='utf-8') as f:
                    from datetime import datetime
                    f.write(f"\n[{datetime.now()}] Application Error: {error_msg}\n")
                    f.write(traceback.format_exc())
                print(f"Error log saved to: {error_log}")
            except:
                pass
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

