# Software Architecture - AI-System-DocAI V5I

## Overview

AI-System-DocAI V5I follows a layered architecture pattern based on Clean Architecture principles, with clear separation of concerns and dependency inversion.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│         Presentation Layer (PyQt6 UI)                   │
│  - ui.py: Main application window                       │
│  - streaming_ui.py: Streaming components                │
├─────────────────────────────────────────────────────────┤
│      Application Layer (Use Cases / Business Logic)     │
│  - reasoning.py: Structured reasoning engine            │
│  - streaming_reasoning.py: Streaming reasoning          │
├─────────────────────────────────────────────────────────┤
│            Domain Layer (Core Business Logic)           │
│  - retrieval.py: Hybrid search (FAISS + BM25)          │
│  - indexer.py: Document indexing and chunking          │
│  - index_manager.py: Index lifecycle management        │
├─────────────────────────────────────────────────────────┤
│     Infrastructure Layer (External Integrations)        │
│  - llm.py: LLM backend integrations                    │
│  - embeddings.py: SentenceTransformers wrapper         │
│  - loaders.py: Document parsers                        │
│  - ingest.py: Document processing                      │
├─────────────────────────────────────────────────────────┤
│      Cross-Cutting Concerns (Configuration & Logging)   │
│  - config.py: Configuration management                 │
│  - enterprise_logging.py: Logging and audit            │
└─────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Document Processing Pipeline

**Flow**: Documents → Loaders → Ingest → Indexer → FAISS Index

- **loaders.py**: Extracts text from various document formats
  - PDF: PyMuPDF (primary) / pypdf (fallback)
  - DOCX: docx2txt
  - PPTX: python-pptx
  - XLSX: pandas
  - TXT/MD/CSV: chardet for encoding detection

- **ingest.py**: Processes documents for indexing
  - Generates document hashes
  - Extracts metadata
  - Prepares documents for chunking

- **indexer.py**: Creates vector index
  - Text chunking (800 chars, 120 char overlap)
  - Embedding generation (CPU-only)
  - FAISS index creation (Flat/HNSW/IVF)
  - Metadata persistence (JSONL format)

### 2. Retrieval System

**Flow**: Query → Embeddings → FAISS Search → BM25 Fusion → Ranked Results

- **retrieval.py**: Hybrid search implementation
  - Dense retrieval: FAISS inner product search
  - Sparse retrieval: BM25 lexical search
  - Score fusion: 60% FAISS + 40% BM25 (configurable)
  - Result reranking and deduplication

- **embeddings.py**: Embedding generation
  - SentenceTransformers wrapper
  - Batch processing (8 docs/batch default)
  - CPU-only operation (forced)
  - Model caching

### 3. Reasoning System

**Flow**: Query + Context → LLM → Structured JSON → UI Display

- **reasoning.py**: Structured reasoning engine
  - Question type identification
  - Entity extraction
  - Reasoning chain generation
  - Confidence scoring
  - Citation extraction

- **streaming_reasoning.py**: Real-time reasoning
  - Streaming LLM integration
  - Progressive answer building
  - Live reasoning chain updates
  - Partial result emission

### 4. LLM Integration

**Supported Backends**:

| Backend       | Type      | Streaming | CPU/GPU   |
|---------------|-----------|-----------|-----------|
| OpenAI        | Cloud API | Yes       | N/A       |
| Anthropic     | Cloud API | No        | N/A       |
| Gemini        | Cloud API | Yes       | N/A       |
| Ollama        | Local API | No        | CPU/GPU   |
| HuggingFace   | Local     | No        | CPU       |
| LlamaCpp      | Local     | No        | CPU       |
| NoLLM         | None      | No        | N/A       |

- **llm.py**: LLM backend abstraction
  - BaseLLM interface
  - Factory pattern for backend creation
  - Error handling and fallbacks
  - Response validation

### 5. User Interface

**Technology**: PyQt6 (Qt 6.6+)

**Main Components**:

- **Indexing Tab**: Document indexing interface
  - Folder selection
  - Model/index type selection
  - Progress tracking
  - Status logging

- **Chat Tab**: Query interface
  - LLM backend selection
  - Question input
  - Streaming/batch mode toggle
  - Answer display with formatting
  - JSON reasoning viewer

- **Index Management Tab**: Index operations
  - List all indexes
  - View index details
  - Delete/rename/rebuild operations
  - Storage statistics

- **Diagnostics Tab**: System monitoring
  - System information display
  - Model configuration
  - Log viewer
  - Refresh controls

### 6. Configuration Management

**Format**: TOML

**Locations**:
- Windows: `%LOCALAPPDATA%/AI-System-DocAI/config.toml`
- Linux: `~/.config/AI-System-DocAI/config.toml`

**Sections**:
- `[app]`: Application metadata
- `[paths]`: Directory locations
- `[llm]`: LLM backend settings
- `[embeddings]`: Embedding model configuration
- `[indexing]`: Chunking and index parameters
- `[retrieval]`: Search and fusion settings
- `[reasoning]`: Reasoning engine parameters
- `[security]`: Security features
- `[enterprise]`: Enterprise features

### 7. Logging System

**Log Types**:

1. **Startup Log**: Application initialization
   - System information
   - Configuration loaded
   - Component initialization

2. **Runtime Log**: Operational events
   - User actions
   - Index operations
   - Query processing
   - Rotating (10MB max, 5 backups)

3. **Error Log**: Errors and exceptions
   - Stack traces
   - Context information
   - Diagnostic data

4. **Audit Log**: Security events
   - Document access
   - Query history
   - Configuration changes
   - IP addresses

## Design Patterns

### 1. Factory Pattern
- **LLM Backend Creation**: `create_llm()` factory function
- **Index Creation**: `_create_index()` for FAISS indexes

### 2. Strategy Pattern
- **Document Loaders**: Different loaders for different file types
- **Index Types**: Flat, HNSW, IVF strategies

### 3. Observer Pattern
- **Qt Signals/Slots**: UI updates from background threads
- **Progress Callbacks**: Indexing progress updates

### 4. Singleton Pattern
- **Config Manager**: `config_manager` global instance
- **Logger**: `enterprise_logger` global instance
- **Embedding Manager**: Lazy-initialized singleton

### 5. Thread Pool Pattern
- **QThread Workers**: Background processing
- **Thread Safety**: Proper signal/slot usage

## Data Flow

### Indexing Flow

```
User selects folder
      ↓
Indexer loads documents
      ↓
Text extraction (loaders.py)
      ↓
Text chunking (800/120)
      ↓
Batch embedding generation
      ↓
FAISS index creation
      ↓
Metadata persistence
      ↓
Index ready for queries
```

### Query Flow

```
User enters question
      ↓
Query embedding generation
      ↓
FAISS similarity search
      ↓
BM25 lexical search
      ↓
Score fusion and ranking
      ↓
Context assembly
      ↓
LLM prompt generation
      ↓
LLM inference
      ↓
Response parsing
      ↓
UI display with citations
```

## Performance Considerations

### CPU Optimization

1. **Batch Processing**: Embeddings processed in batches (8 default)
2. **Index Selection**: HNSW for speed, Flat for accuracy
3. **Chunking Strategy**: Balanced chunk size (800 chars)
4. **Memory Management**: Explicit garbage collection
5. **Threading**: Background workers for heavy operations

### Memory Management

- **Index Loading**: Lazy loading of retriever
- **Model Caching**: SentenceTransformers cached in memory
- **Document Streaming**: Large files processed in chunks
- **Log Rotation**: Automatic log file rotation

### Scalability

**Current Limits**:
- Documents: 10,000+ per index
- Vectors: 1,000,000+ vectors
- Query Speed: <1s for 100K vectors (HNSW)
- Indexing Speed: ~100 docs/minute (CPU)

**Bottlenecks**:
- Embedding generation (CPU-bound)
- Large PDF parsing (I/O-bound)
- LLM inference (API latency)

## Security Architecture

### Input Validation
- File path sanitization
- Query string validation
- Configuration validation

### Data Protection
- Local storage only
- No external API calls (configurable)
- File permissions enforcement

### Audit Trail
- Operation logging
- IP address tracking
- Timestamp recording

## Testing Strategy

### Unit Tests
- Document loaders
- Chunking algorithms
- Embedding generation
- Score fusion

### Integration Tests
- End-to-end indexing
- Query pipeline
- LLM backends
- UI interactions

### Performance Tests
- Indexing speed
- Query latency
- Memory usage
- Concurrent operations

## Future Enhancements

1. **Multi-Index Querying**: Search across multiple indexes
2. **Advanced Reranking**: Cross-encoder reranking
3. **OCR Support**: Extract text from scanned documents
4. **Export Features**: Export answers to various formats
5. **API Server**: RESTful API for programmatic access
6. **Advanced Security**: Authentication and encryption

## Technology Stack

### Core
- Python 3.8+
- PyQt6 6.6+
- FAISS (CPU) 1.7.4+

### ML/AI
- SentenceTransformers 2.2.2+
- PyTorch 2.0+ (CPU-only)
- Transformers 4.30+

### Document Processing
- PyMuPDF 1.22.5+
- pypdf 3.15+
- docx2txt 0.8+
- python-pptx 0.6.21+

### Utilities
- rank-bm25 0.2.2+
- toml 0.10.2+
- psutil 5.9.5+
- chardet 5.1.0+

## Deployment Architecture

### Standalone Mode
```
User Machine
├── Application Files
├── Virtual Environment
├── Local Indexes
├── Local Cache
└── Configuration
```

### Internal LAN Mode
```
File Server (Documents)
      ↓
Application Server (Indexing)
      ↓
Client Machines (Query)
```

## Maintenance

### Regular Tasks
- Log rotation: Daily
- Index optimization: Weekly
- Dependency updates: Monthly
- Security reviews: Quarterly

### Monitoring
- Disk space usage
- Memory consumption
- Index size growth
- Query performance

## Support and Documentation

- User Guide: `docs/README.md`
- Installation: `docs/INSTALL.md`
- Security: `docs/SECURITY.md`
- API Reference: In-code docstrings
- Logs: `logs/` directory

