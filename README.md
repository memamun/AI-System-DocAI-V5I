# AI-System-DocAI V5I - Enterprise Edition

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CPU Only](https://img.shields.io/badge/CPU-Only-green.svg)](https://github.com/)

## 🚀 Overview

AI-System-DocAI V5I is an **offline AI-assisted document reasoning system** designed for enterprise environments. It provides semantic search, contextual reasoning, and structured Q&A capabilities across multiple document formats with **100% CPU-only operation**.

### Key Features

- ✅ **100% Offline**: No cloud dependencies, all processing happens locally
- 🖥️ **CPU-Only Architecture**: No GPU required
- 📄 **Multi-Format Support**: PDF, DOCX, TXT, XLSX, PPTX
- 🔍 **Hybrid Search**: FAISS vector search + BM25 lexical search
- 🤖 **Multiple LLM Backends**: OpenAI, Anthropic, Gemini, Ollama, HuggingFace, LlamaCpp
- 💭 **Live Thinking Mode**: Real-time streaming of reasoning process
- 📊 **Structured Reasoning**: JSON-formatted answers with citations and confidence scores
- 🔒 **Enterprise Security**: Audit logging, IP filtering, rate limiting
- 🎨 **Professional UI**: PyQt6-based desktop application

## 📋 System Requirements

### Minimum
- **CPU**: 4-core processor
- **RAM**: 16 GB
- **Disk**: 5 GB free space
- **OS**: Windows 10/11 or Linux (Ubuntu 20.04+)
- **Python**: 3.8+

### Recommended
- **CPU**: 8-core processor
- **RAM**: 32 GB
- **Disk**: 20 GB SSD
- **Python**: 3.10+

## 🚀 Quick Start

### Windows
```batch
# Download and extract
# Double-click launcher.bat
launcher.bat
```

### Linux
```bash
# Extract archive
tar -xzf AI-System-DocAI-V5I.tar.gz
cd AI-System-DocAI-V5I

# Run launcher
chmod +x launcher.sh
./launcher.sh
```

First run will automatically:
1. Create virtual environment
2. Install dependencies
3. Launch the application

## 📖 Documentation

- **[User Guide](docs/README.md)**: Complete usage instructions
- **[Installation Guide](docs/INSTALL.md)**: Detailed installation steps
- **[Security Guidelines](docs/SECURITY.md)**: Security best practices
- **[Architecture](docs/ARCHITECTURE.md)**: Technical architecture overview

## 🎯 Usage

### 1. Index Documents
1. Go to **Indexing** tab
2. Select folder with documents
3. Click **Build Index**
4. Wait for completion

### 2. Configure LLM
1. Go to **Chat** tab
2. Select LLM backend
3. Click **Configure** (set API key if needed)
4. Click **Apply**

### 3. Ask Questions
1. Type your question
2. Enable **Live Thinking** for streaming (optional)
3. Click **Search and Answer**
4. View results with citations

## 🔧 Configuration

Configuration file location:
- **Windows**: `%LOCALAPPDATA%\AI-System-DocAI\config.toml`
- **Linux**: `~/.config/AI-System-DocAI/config.toml`

### Example Configuration

```toml
[llm]
backend = "openai"
model_type = "gpt-4o-mini"
temperature = 0.7
max_tokens = 600

[embeddings]
model = "sentence-transformers/all-MiniLM-L6-v2"
device = "cpu"
batch_size = 8

[security]
internal_lan_mode = true
audit_logging = true
rate_limit_per_ip = 100
```

## 🐛 Troubleshooting

### Dependencies Not Installing
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### LLM Backend Errors
1. Verify API key is set correctly
2. Check internet connection (for cloud APIs)
3. Try "No LLM" mode to test retrieval only

### Performance Issues
1. Use MiniLM-L6-v2 embedding model (faster)
2. Use HNSW index type
3. Reduce chunk size in config

## 📦 Project Structure

```
AI-System-DocAI-V5I/
├── src/                    # Core application modules
│   ├── ui.py              # PyQt6 UI
│   ├── reasoning.py       # Reasoning engine
│   ├── retrieval.py       # Hybrid search
│   ├── indexer.py         # Document indexing
│   ├── llm.py             # LLM backends
│   └── ...
├── docs/                  # Documentation
├── installer/             # Installer scripts
├── assets/                # Icons and resources
├── main.py               # Application entry point
├── launcher.py           # Cross-platform launcher
├── launcher.bat          # Windows launcher
├── launcher.sh           # Linux launcher
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔒 Security

- 100% offline operation (except cloud LLM APIs)
- No telemetry or data collection
- Audit logging for all operations
- IP filtering and rate limiting
- See [SECURITY.md](docs/SECURITY.md) for details

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For issues, questions, or feature requests:
1. Check documentation in `docs/` directory
2. Review logs in `logs/` directory
3. Contact your system administrator

## 🏗️ Build & Distribution

### Windows Installer
```batch
# Requires Inno Setup
iscc installer\windows_installer.iss
```

### Linux Packages
```bash
# Debian/Ubuntu
./installer/build_deb.sh

# Fedora/RHEL
./installer/build_rpm.sh
```

## 🎖️ Credits

- Built with PyQt6, FAISS, SentenceTransformers
- Uses various LLM APIs (OpenAI, Anthropic, Google, etc.)
- Document processing: PyMuPDF, pypdf, docx2txt, python-pptx

## 📊 Version History

- **5I.2025** (Current): CPU-only enterprise edition with internal LAN security
- CPU-only architecture
- Enhanced security features
- Improved documentation
- Comprehensive installers

---

**AI-System-DocAI V5I** - Empowering document reasoning with AI, 100% offline.

