# Implementation Details: Intelligent Document Chunking

## Architecture Overview

### System Components

```
Document Source
    ↓
Loader (loaders.py)
    ↓ [Returns: (text, page_number)]
    ↓
Indexer (indexer.py)
    ↓
ContextualChunker (chunking.py)
    ↓ [Intelligent Processing]
    ├─ Structural Analysis
    ├─ Semantic Splitting
    ├─ Type Classification
    └─ Metadata Enrichment
    ↓ [Returns: Rich Chunks]
    ↓
Embedding & Indexing
    ↓
FAISS Index
```

## Core Algorithm

### 1. Structural Analysis Phase
```python
def _extract_sections(text: str) -> List[Dict]:
    """
    Identifies:
    - Markdown headings (# ## ###)
    - Numbered sections (1. 2.1.3)
    - Section labels (4.2.5 Wi-Fi Security)
    
    Output: List of section boundaries with hierarchy levels
    """
```

**Key Patterns Detected**:
- Markdown headings: `^#+\s+`
- Numbered sections: `^\d+\.`
- Section headers: `^[A-Z][A-Za-z\s]+:`

### 2. Semantic Splitting Phase
```python
def _split_by_sentences(text: str) -> List[Tuple[int, int, str]]:
    """
    Identifies sentence boundaries:
    - Ends with . ! ? followed by space and capital letter
    - Paragraph breaks (double newlines)
    - List item transitions
    
    Returns: List of (start_pos, end_pos, sentence_text)
    """
```

**Boundary Detection**:
- Sentence endings: `(?<=[.!?])\s+(?=[A-Z])`
- Paragraph breaks: `\n\n+`
- List items: Before bullet points or numbers

### 3. Intelligent Merging Phase
```python
def _create_intelligent_chunks(...):
    """
    Combines sentences into semantic units:
    1. Start new chunk for section changes
    2. Add sentences until reaching chunk_size
    3. Maintain minimum chunk size
    4. Add contextual overlap from previous chunk
    
    Returns: List of semantic chunks with metadata
    """
```

**Algorithm**:
```
for each sentence:
    if new_section_detected:
        save_current_chunk()
        start_new_chunk_for_section()
    elif current_chunk + sentence < chunk_size:
        add_sentence_to_current_chunk()
    else:
        save_current_chunk()
        create_overlap_from_previous()
        start_new_chunk_with_current_sentence()

save_remaining_chunk()
```

### 4. Chunk Classification Phase
```python
def _detect_chunk_type(text: str) -> str:
    """
    Classifies chunk based on content patterns:
    
    - heading: Contains markdown/section headers
    - procedure: Numbered steps or procedure markers
    - definition: Contains "is", "means", "defined as"
    - code: Contains code block markers or indentation
    - table: Contains pipe-delimited columns
    - reasoning: Contains causal keywords
    - standard: Regular body text
    """
```

**Classification Rules**:
| Type | Pattern |
|------|---------|
| heading | `^#+\s` or `^[A-Z].*:` |
| procedure | `^\d+\.\s` or `step\s+\d+:` |
| definition | `is\s+(?:a\|the)` or `defined as` |
| code | ` ```  ` or 4+ space indent |
| table | `\|.*\|.*\|` |
| reasoning | `because` or `therefore` |

### 5. PDF-Specific Processing
```python
def chunk_pdf_smart(pdf_path: Path, page_num: int):
    """
    PyMuPDF Enhanced PDF Chunking:
    
    1. Extract text dictionary from PDF
    2. Iterate through text blocks
    3. Detect formatting (bold = heading, mono = code)
    4. Preserve block structure
    5. Merge small adjacent blocks
    6. Classify block type
    """
```

**PDF Feature Detection**:
- **Headings**: Bold text (flag & 1 = True)
- **Code**: Monospace fonts (font.startswith("mono"))
- **Structure**: Original block positions
- **Layout**: Preserve reading order

## Configuration Parameters

### Main Settings

```python
chunk_size: int = 1000
    # Target chunk size in characters
    # Increase for more context: 1200-1500
    # Decrease for granularity: 800-900
    # Default: 1000 (good balance)

chunk_overlap: int = 200
    # Overlap between chunks in characters
    # Increase for smooth transitions: 250-300
    # Decrease for independence: 100-150
    # Default: 200 (recommended)

min_chunk_size: int = 100
    # Minimum size to prevent tiny fragments
    # Prevents indexing of stub text
    # Rarely needs adjustment
    # Default: 100

intelligent_chunking: bool = True
    # Enable/disable semantic boundary detection
    # Always recommended: True
    # Can disable for legacy behavior: False
    # Default: True
```

## Metadata Structure

### Per-Chunk Metadata
```python
{
    "text": str,              # Actual chunk content
    "page": int,              # Page number (1-based, actual)
    "chunk_type": str,        # Classification (see above)
    "section": Optional[str], # Parent section heading
    "hierarchy": int,         # Nesting level (0, 1, 2...)
    "file": str,              # Full file path
    "doc_id": str,            # Hash for document ID
    "length": int,            # Character count
    "sentence_count": int,    # Number of sentences
}
```

### Metadata Usage
- **BM25**: Uses text content and section
- **Embedding**: Uses full chunk text
- **Retrieval**: Uses all metadata for filtering
- **Citation**: Uses page, section, file
- **Context**: Uses hierarchy and related chunks

## Integration with Other Components

### With Retriever
```python
# Old: Direct text retrieval
chunks = retriever.search(query, k=12)

# New: Rich metadata with retrieval
chunks = retriever.search(query, k=12)
# Now includes: chunk_type, section, hierarchy
```

### With LLM Reasoning
```python
# Chunks now provide:
1. Complete semantic units (not split mid-thought)
2. Section context for understanding hierarchy
3. Chunk type hints for better interpretation
4. Sufficient overlap for context flow

# LLM can use this for:
1. Better understanding of document structure
2. Smarter reasoning on complete thoughts
3. More accurate citations
4. Better answer synthesis
```

### With Embeddings
```python
# Before: Many fragmented chunks with weak embeddings
# After: Fewer but semantically stronger chunks
#        Better embedding quality due to coherence

# Result:
1. Better semantic similarity matching
2. More relevant chunk retrieval
3. Improved embedding quality
4. Better BM25 scoring
```

## Performance Characteristics

### Time Complexity
- **Chunking**: O(n) where n = text length
- **Section detection**: O(n) with regex
- **Sentence splitting**: O(n) with regex
- **Merging**: O(m) where m = number of chunks
- **Overall**: O(n + m) linear

### Space Complexity
- **Metadata storage**: O(m) for m chunks
- **Section tracking**: O(s) for s sections
- **Overlap buffers**: O(k) where k = overlap size
- **Overall**: O(m + s) linear

### Practical Performance
- **Per-document**: ~1-2 seconds for smart chunking
- **Per-page**: ~100-200ms for PDF extraction
- **Index growth**: ~5-10% larger for metadata
- **Query time**: No change (same retrieval)

## Error Handling

### Graceful Degradation
```python
# If smart PDF processing fails:
try:
    chunks = chunk_pdf_smart(path, page_num)
except ImportError:
    logger.warning("PyMuPDF not available, using text chunks")
    chunks = smart_chunk_text(text, page_num)

# If section detection fails:
try:
    sections = extract_sections(text)
except:
    sections = []  # Continue without sections
    
# If chunk classification fails:
try:
    chunk_type = detect_chunk_type(text)
except:
    chunk_type = "standard"  # Default to standard
```

## Optimization Tips

### For Large Documents
```python
# Increase chunk size slightly
chunk_size: 1200  # More content per chunk
overlap: 200      # Maintain overlap

# Reduces total chunks, speeds up embedding
```

### For Technical Content
```python
chunk_size: 1100   # Enough for code + context
overlap: 250       # Important for code flow
```

### For Memory-Constrained Systems
```python
chunk_size: 800    # Smaller chunks
overlap: 150       # Still reasonable overlap
# Trade-off: More chunks, less memory per chunk
```

### For Quality Over Performance
```python
chunk_size: 1500   # Very complete chunks
overlap: 300       # Maximum context
# Trade-off: Fewer chunks, slower indexing
```

## Testing & Validation

### Verify Chunking Quality
```python
from chunking import ContextualChunker

chunker = ContextualChunker()
chunks = chunker.chunk(your_text, page_num)

# Check:
for chunk in chunks:
    print(f"Type: {chunk['chunk_type']}")
    print(f"Length: {chunk['length']}")
    print(f"Section: {chunk['section']}")
    print(f"Text: {chunk['text'][:100]}...")
```

### Verify Metadata
```python
import json

with open('faiss_index/meta.jsonl', 'r') as f:
    for line in f:
        meta = json.loads(line)
        # Check all expected fields are present
        assert 'chunk_type' in meta
        assert 'section' in meta
        assert 'hierarchy' in meta
```

### Performance Testing
```python
import time

chunker = ContextualChunker()
start = time.time()

for text, page_num in documents:
    chunks = chunker.chunk(text, page_num)

duration = time.time() - start
print(f"Processed in {duration:.2f}s")
print(f"Rate: {len(documents) / duration:.1f} doc/s")
```

## Future Enhancements

### Planned Improvements
1. **Entity Extraction**: Named entity recognition per chunk
2. **Summarization**: Auto-generate chunk summaries
3. **Linking**: Cross-document chunk relationships
4. **Hierarchy**: Explicit parent-child relationships
5. **Semantic**: Similarity-based chunk optimization

### Experimental Features
- Multi-level chunking (summary + detailed)
- Domain-specific chunk optimization
- Automatic parameter tuning
- Chunk quality scoring
- Adaptive chunking based on content

## References & Resources

### Documentation
- `CHUNKING_STRATEGY.md`: Conceptual overview
- `CHUNKING_IMPROVEMENTS.md`: Quick reference
- `UPGRADE_SUMMARY.md`: Migration guide

### Code Files
- `src/chunking.py`: Main implementation
- `src/indexer.py`: Integration point
- `src/config.py`: Configuration

### External Resources
- [Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Semantic Search](https://huggingface.co/blog/semantic-search-hf)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-13  
**Audience**: Developers and Advanced Users

