# AI-System-DocAI V5I - Enterprise Edition

## Overview

AI-System-DocAI V5I is an offline AI-assisted document reasoning system designed for enterprise environments. It provides semantic search, contextual reasoning, and structured Q&A capabilities across PDF, DOCX, TXT, XLSX, and PPTX documents.

## Key Features

- **100% Offline Operation**: No cloud dependencies, all processing happens locally
- **CPU-Only Architecture**: Optimized for CPU operation (no GPU required)
- **Multiple LLM Backends**: Supports OpenAI-compatible APIs, Anthropic Claude, Google Gemini, Ollama, HuggingFace, and LlamaCpp
- **Hybrid Search**: Combines FAISS vector search with BM25 for optimal retrieval
- **Structured Reasoning**: Generates JSON-formatted answers with reasoning chains, confidence scores, and citations
- **Live Thinking Mode**: Real-time streaming of the LLM's reasoning process
- **Enterprise Logging**: Comprehensive audit trails and performance monitoring
- **Internal LAN Security**: Built-in security features for internal network deployment

## System Requirements

### Minimum
- CPU: 4-core processor
- RAM: 16 GB
- Disk: 5 GB free space
- OS: Windows 10/11 or Linux (Ubuntu 20.04+, Fedora 35+)
- Python: 3.8 or later

### Recommended
- CPU: 8-core processor
- RAM: 32 GB
- Disk: 20 GB free space (SSD preferred)
- OS: Windows 11 or Linux (Ubuntu 22.04+)
- Python: 3.10 or later

## Quick Start

### Windows
1. Double-click `launcher.bat`
2. Wait for dependencies to install (first run only)
3. The application will launch automatically

### Linux
1. Open terminal in the installation directory
2. Run: `./launcher.sh`
3. Wait for dependencies to install (first run only)
4. The application will launch automatically

## Usage Guide

### 1. Indexing Documents

1. Go to the **Indexing** tab
2. Click **Choose Folder** and select a folder containing your documents
3. Select embedding model (default: MiniLM-L6-v2)
4. Select index type (default: HNSW)
5. Click **Build Index**

### 2. Configuring LLM Backend

1. Go to the **Chat** tab
2. Select LLM backend from dropdown:
   - **OpenAI / Compatible API**: For OpenAI or OpenRouter
   - **Anthropic Claude**: For Claude models
   - **Google Gemini**: For Gemini models
   - **Ollama**: For local Ollama server
   - **HuggingFace Local**: For local HF models
   - **LlamaCpp**: For GGUF models
   - **No LLM**: Citations only mode
3. Click **Configure** to set API keys or model paths
4. Click **Apply** to activate the backend

### 3. Asking Questions

1. Ensure an index is loaded (check status bar)
2. Type your question in the text box
3. Enable **Live Thinking** for streaming mode (optional)
4. Click **Search and Answer**
5. View the answer and reasoning details

### 4. Managing Indexes

1. Go to the **Index Management** tab
2. View all available indexes with their statistics
3. Select an index to view details
4. Use buttons to:
   - **Refresh**: Update the index list
   - **Delete**: Remove selected indexes
   - **Delete All**: Remove all indexes
   - **Rebuild**: Rebuild an index from source documents
   - **Rename**: Change an index name

### 5. Diagnostics

1. Go to the **Diagnostics** tab
2. View system information, model status, and logs
3. Use buttons to:
   - **Refresh**: Update all information
   - **Reveal Logs**: Open logs directory
   - **View Logs**: View logs in a dialog

## Configuration

Configuration is stored in:
- **Windows**: `%LOCALAPPDATA%\AI-System-DocAI\config.toml`
- **Linux**: `~/.config/AI-System-DocAI/config.toml`

Edit this file to customize:
- Default LLM backend and model
- Embedding model
- Chunk sizes and overlap
- Retrieval parameters
- Security settings

## Troubleshooting

### Dependencies Not Installing

**Problem**: Dependencies fail to install during first launch

**Solution**:
1. Ensure Python 3.8+ is installed and in PATH
2. Ensure internet connection for downloading packages
3. Run manually: `pip install -r requirements.txt`
4. Check logs in `logs/` directory

### Index Build Fails

**Problem**: Indexing process fails or hangs

**Solution**:
1. Check that documents are in supported formats (PDF, DOCX, TXT, XLSX, PPTX)
2. Ensure sufficient disk space (5+ GB)
3. Try with a smaller set of documents first
4. Check logs for specific error messages

### LLM Backend Errors

**Problem**: LLM backend fails to respond

**Solution**:
1. Verify API keys are set correctly (for cloud APIs)
2. Check internet connection (for cloud APIs)
3. Verify Ollama server is running (for Ollama backend)
4. Try "No LLM" mode to test retrieval without LLM

### Performance Issues

**Problem**: Application is slow

**Solution**:
1. Use MiniLM-L6-v2 embedding model (faster)
2. Reduce chunk size in config
3. Use HNSW index type (faster than Flat)
4. Ensure SSD is used for index storage
5. Close other memory-intensive applications

## Security Notes

- This application is designed for internal LAN use
- No data is sent to external servers (except when using cloud LLM APIs)
- All audit logs are stored locally
- API keys are stored in plain text in config file (secure your system accordingly)
- Consider using "No LLM" mode for maximum privacy

## Support

For issues, questions, or feature requests:
- Check the documentation in `docs/` directory
- Review logs in `logs/` directory
- Contact your system administrator

## License

See `LICENSE` file for details.

## Version Information

- Version: 5I.2025
- Publisher: AI-System-Solutions
- Release Date: October 2025

