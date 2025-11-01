# Installation Guide - AI-System-DocAI V5I

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Windows Installation](#windows-installation)
3. [Linux Installation](#linux-installation)
4. [Manual Installation](#manual-installation)
5. [Verification](#verification)
6. [Uninstallation](#uninstallation)

## Prerequisites

### All Platforms

- **Python 3.8 or later** (3.10+ recommended)
- **16 GB RAM minimum** (32 GB recommended)
- **5 GB free disk space** (20 GB recommended)
- **Internet connection** (for initial setup only)

### Windows

- Windows 10 or Windows 11
- PowerShell 5.1 or later (included in Windows 10/11)

### Linux

- Ubuntu 20.04+ or Fedora 35+ (or equivalent)
- bash shell
- Standard build tools: `python3-dev`, `python3-venv`, `python3-pip`

## Windows Installation

### Option 1: Using Installer (Recommended)

1. Download `AI-System-DocAI-V5I-Setup.exe`
2. Double-click the installer
3. Follow the installation wizard
4. Choose installation directory (default: `C:\Program Files\AI-System-DocAI`)
5. Optionally create desktop shortcut
6. Click "Install"
7. Launch from Start Menu or Desktop

### Option 2: Portable Version

1. Extract `AI-System-DocAI-V5I.zip` to desired location
2. Double-click `launcher.bat`
3. Wait for initial setup (creates virtual environment and installs dependencies)
4. Application will launch automatically

### Manual Setup (Windows)

```batch
# 1. Extract files
cd C:\path\to\AI-System-DocAI-V5I

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.venv\Scripts\activate.bat

# 4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Launch application
python main.py
```

## Linux Installation

### Option 1: Using Package Manager (Debian/Ubuntu)

```bash
# Download the .deb package
wget https://example.com/ai-system-docai_5I.2025_amd64.deb

# Install the package
sudo dpkg -i ai-system-docai_5I.2025_amd64.deb

# Install dependencies if needed
sudo apt-get install -f

# Launch application
ai-system-docai
```

### Option 2: Using Package Manager (Fedora/RHEL)

```bash
# Download the .rpm package
wget https://example.com/ai-system-docai-5I.2025.x86_64.rpm

# Install the package
sudo rpm -ivh ai-system-docai-5I.2025.x86_64.rpm

# Or using dnf
sudo dnf install ai-system-docai-5I.2025.x86_64.rpm

# Launch application
ai-system-docai
```

### Option 3: Portable Version

```bash
# 1. Extract files
tar -xzf AI-System-DocAI-V5I.tar.gz
cd AI-System-DocAI-V5I

# 2. Make launcher executable
chmod +x launcher.sh

# 3. Run launcher
./launcher.sh

# First run will create venv and install dependencies
```

### Manual Setup (Linux)

```bash
# 1. Navigate to directory
cd /path/to/AI-System-DocAI-V5I

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Launch application
python main.py
```

## Environment Variables

### Required for OpenAI Backend

Set this before launching if using OpenAI API:

#### OpenAI / OpenRouter
```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
```

**Note:** Ollama and HuggingFace run locally and don't require API keys.

### Windows
Set via System Properties > Environment Variables or:
```batch
setx OPENAI_API_KEY "your-api-key-here"
```

### Linux
Add to `~/.bashrc` or `~/.profile`:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Verification

### Check Installation

1. Launch the application
2. Check **Diagnostics** tab:
   - System information should display correctly
   - Device should show "CPU Mode"
   - Python version should be 3.8+
3. Check logs directory:
   - Should contain `AI-System-DocAI_Startup.log`
   - Log should show successful initialization

### Test Indexing

1. Go to **Indexing** tab
2. Select a folder with a few documents
3. Click **Build Index**
4. Process should complete without errors
5. Index status should show number of vectors

### Test Query

1. Go to **Chat** tab
2. Select an LLM backend (Ollama recommended for testing)
3. Click **Apply**
4. Ask a question about your indexed documents
5. Should return answer with citations from relevant documents

## Troubleshooting

### Python Not Found

**Windows**:
1. Download Python from python.org
2. Install with "Add to PATH" option checked
3. Restart terminal/command prompt

**Linux**:
```bash
sudo apt-get install python3 python3-venv python3-pip  # Ubuntu/Debian
sudo dnf install python3 python3-pip  # Fedora
```

### Permission Errors

**Windows**:
- Run installer as Administrator
- Ensure antivirus isn't blocking files

**Linux**:
```bash
# If installed to /opt
sudo chown -R $USER:$USER /opt/ai-system-docai

# Or install to home directory
./launcher.sh  # Will create .venv in current directory
```

### Dependency Installation Fails

1. Check internet connection
2. Update pip:
   ```bash
   python -m pip install --upgrade pip
   ```
3. Try installing dependencies one by one:
   ```bash
   pip install PyQt6
   pip install sentence-transformers
   pip install faiss-cpu
   # etc.
   ```

## Uninstallation

### Windows (Installed)
1. Go to Settings > Apps
2. Find "AI-System-DocAI"
3. Click Uninstall

### Windows (Portable)
1. Delete the application folder
2. Delete config: `%LOCALAPPDATA%\AI-System-DocAI`

### Linux (Package)
```bash
sudo apt-get remove ai-system-docai  # Debian/Ubuntu
sudo dnf remove ai-system-docai      # Fedora
```

### Linux (Portable)
```bash
# Delete application directory
rm -rf /path/to/AI-System-DocAI-V5I

# Delete config
rm -rf ~/.config/AI-System-DocAI
```

## Next Steps

After installation, refer to:
- `README.md` for usage guide
- `SECURITY.md` for security guidelines
- `ARCHITECTURE.md` for technical details

## Support

For installation issues:
1. Check logs in `logs/` directory
2. Verify system meets minimum requirements
3. Contact your system administrator

