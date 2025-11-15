"""
Intelligent Document Chunking for RAG
Preserves semantic boundaries, document structure, and contextual information
"""
from __future__ import annotations
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ContextualChunker:
    """Intelligent chunking that preserves document structure and semantics"""

    def __init__(self, chunk_size: int = 1000, overlap: int = 150, min_chunk_size: int = 100):
        """
        Initialize the chunker with configurable parameters
        
        Args:
            chunk_size: Target size for chunks (characters)
            overlap: Overlap between chunks for context preservation
            min_chunk_size: Minimum chunk size to avoid tiny fragments
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        
        # Patterns for structural elements
        self.heading_pattern = re.compile(r'^#+\s+|^[A-Z][A-Za-z\s]+:$', re.MULTILINE)
        self.section_pattern = re.compile(r'^\d+\..*?:|^[IVXLCDM]+\..*?:', re.MULTILINE)
        self.list_pattern = re.compile(r'^\s*[-•*]\s+|^\s*\d+\.\s+', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```[\s\S]*?```|^\s{4,}.*$', re.MULTILINE)
        self.table_pattern = re.compile(r'\|.*?\|.*?\|')

    def chunk(self, text: str, page_num: int, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Intelligently chunk text while preserving semantic and structural information
        
        Args:
            text: Text to chunk
            page_num: Page number for tracking
            metadata: Additional metadata to include
            
        Returns:
            List of chunk dictionaries with text, metadata, and hierarchy info
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            return [{
                "text": text.strip(),
                "page": page_num,
                "chunk_type": "short",
                "section": None,
                "hierarchy": 0,
                **(metadata or {})
            }]

        # Step 1: Identify structural boundaries
        sections = self._extract_sections(text)

        # Step 2: Split by semantic boundaries
        sentences = self._split_by_sentences(text)

        # Step 3: Create intelligent chunks
        chunks = self._create_intelligent_chunks(text, sentences, sections, page_num, metadata)

        return chunks

    def _extract_sections(self, text: str) -> List[Dict]:
        """Extract document structure (headings, sections)"""
        sections = []
        
        # Find headings and section markers
        for match in re.finditer(r'^(#+\s+)(.+?)$|^(\d+\.\s+)(.+?)$|^([A-Z][A-Za-z\s]+:)\s*$', text, re.MULTILINE):
            sections.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0),
                'level': len(match.group(1) or match.group(3) or '') if match.group(1) or match.group(3) else 0
            })

        return sections

    def _split_by_sentences(self, text: str) -> List[Tuple[int, int, str]]:
        """Split text into sentences while preserving positions"""
        # Enhanced sentence splitting that handles special cases
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s+(?=\d+\.)|\n\n+'
        
        sentences = []
        current_pos = 0
        
        for match in re.finditer(sentence_endings, text):
            sentence_text = text[current_pos:match.start()].strip()
            if sentence_text:
                sentences.append((current_pos, match.start(), sentence_text))
            current_pos = match.end()
        
        # Add remaining text
        remaining = text[current_pos:].strip()
        if remaining:
            sentences.append((current_pos, len(text), remaining))
        
        return sentences

    def _create_intelligent_chunks(self, text: str, sentences: List[Tuple[int, int, str]], 
                                  sections: List[Dict], page_num: int, 
                                  metadata: Optional[Dict] = None) -> List[Dict]:
        """Create semantic chunks by combining sentences intelligently"""
        chunks = []
        current_chunk = ""
        current_section = None
        chunk_start_pos = 0
        
        for sent_start, sent_end, sentence in sentences:
            # Detect section changes
            new_section = self._get_section_for_position(sent_start, sections)
            if new_section and new_section != current_section:
                # Save current chunk if it exists
                if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
                    chunks.append(self._create_chunk_dict(
                        current_chunk.strip(), page_num, current_section, metadata
                    ))
                # Start new chunk for new section
                current_chunk = sentence + " "
                current_section = new_section
                chunk_start_pos = sent_start
            elif len(current_chunk) + len(sentence) < self.chunk_size:
                # Add to current chunk
                current_chunk += sentence + " "
            else:
                # Current chunk is full, save it and start new one
                if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
                    chunks.append(self._create_chunk_dict(
                        current_chunk.strip(), page_num, current_section, metadata
                    ))
                # Start new chunk with overlap
                current_chunk = self._create_overlap_context(text, chunk_start_pos, sent_end) + sentence + " "
                chunk_start_pos = sent_start
        
        # Save final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append(self._create_chunk_dict(
                current_chunk.strip(), page_num, current_section, metadata
            ))
        
        return chunks

    def _get_section_for_position(self, pos: int, sections: List[Dict]) -> Optional[str]:
        """Get the current section for a given position in text"""
        for section in reversed(sections):
            if section['start'] <= pos:
                return section['text']
        return None

    def _create_overlap_context(self, text: str, start_pos: int, end_pos: int) -> str:
        """Create overlap context from previous chunk"""
        overlap_start = max(0, start_pos - self.overlap)
        overlap_text = text[overlap_start:end_pos]
        
        # Clean up to start with a complete sentence
        first_sentence_end = re.search(r'[.!?]', overlap_text)
        if first_sentence_end:
            overlap_text = overlap_text[first_sentence_end.end():].strip()
        
        return overlap_text

    def _create_chunk_dict(self, text: str, page_num: int, section: Optional[str] = None,
                         metadata: Optional[Dict] = None) -> Dict:
        """Create a chunk dictionary with all metadata"""
        chunk_type = self._detect_chunk_type(text)
        
        return {
            "text": text,
            "page": page_num,
            "chunk_type": chunk_type,
            "section": section,
            "hierarchy": 0,
            "length": len(text),
            "sentence_count": len(re.split(r'[.!?]+', text.strip())),
            **(metadata or {})
        }

    def _detect_chunk_type(self, text: str) -> str:
        """Detect the type of chunk (definition, procedure, explanation, etc.)"""
        text_lower = text.lower()
        
        if re.search(r'^\d+\.\s|^step\s+\d+:|^procedure:', text_lower):
            return "procedure"
        elif re.search(r'is\s+(?:a|the|an)|definition|defined as', text_lower):
            return "definition"
        elif re.search(r'```|^\s{4,}|\t', text):
            return "code"
        elif re.search(r'\|.*\|.*\|', text):
            return "table"
        elif re.search(r'because|therefore|thus|as a result|consequently', text_lower):
            return "reasoning"
        elif len(text) < 100:
            return "short"
        else:
            return "standard"

    def chunk_pdf_smart(self, pdf_path: Path, page_num: int) -> List[Dict]:
        """
        Smart PDF chunking using layout information from PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number in the PDF
            
        Returns:
            List of intelligently chunked passages with structure preserved
        """
        try:
            import fitz  # PyMuPDF
            
            chunks = []
            with fitz.open(str(pdf_path)) as doc:
                if page_num - 1 >= len(doc):
                    return []
                
                page = doc[page_num - 1]
                
                # Extract text with layout information
                text_dict = page.get_text("dict")
                
                # Process blocks while preserving structure
                for block in text_dict.get("blocks", []):
                    if block["type"] == 0:  # Text block
                        block_text = ""
                        block_type = "text"
                        
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span["text"]
                                block_text += text
                                
                                # Detect formatting
                                if span.get("flags", 0) & 1:  # Bold
                                    block_type = "heading"
                                if span.get("font", "").lower().startswith("mono"):
                                    block_type = "code"
                        
                        if block_text.strip():
                            chunks.append({
                                "text": block_text.strip(),
                                "page": page_num,
                                "chunk_type": block_type,
                                "section": None,
                                "hierarchy": 1 if block_type == "heading" else 0
                            })
                    
                    elif block["type"] == 1:  # Image - could extract OCR or metadata
                        pass
                
                # Merge nearby small chunks for better context
                merged_chunks = self._merge_small_chunks(chunks)
                return merged_chunks
                
        except ImportError:
            logger.warning("PyMuPDF (fitz) not available for smart PDF chunking")
            return []

    def _merge_small_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Merge small chunks with surrounding chunks for better context"""
        if len(chunks) <= 1:
            return chunks
        
        merged = []
        i = 0
        
        while i < len(chunks):
            chunk = chunks[i].copy()
            
            # If chunk is too small and not a heading, try to merge with next
            if (len(chunk["text"]) < self.min_chunk_size and 
                chunk["chunk_type"] != "heading" and 
                i + 1 < len(chunks)):
                
                next_chunk = chunks[i + 1]
                chunk["text"] = chunk["text"] + "\n\n" + next_chunk["text"]
                chunk["length"] = len(chunk["text"])
                i += 2
            else:
                i += 1
            
            merged.append(chunk)
        
        return merged


# Utility function for simple semantic chunking (for non-PDF documents)
def smart_chunk_text(text: str, page_num: int, chunk_size: int = 1000, 
                    overlap: int = 150) -> List[Dict]:
    """
    Perform smart chunking on text content
    
    Args:
        text: Text to chunk
        page_num: Page number for reference
        chunk_size: Target chunk size in characters
        overlap: Overlap size between chunks
        
    Returns:
        List of intelligently chunked passages
    """
    chunker = ContextualChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk(text, page_num)

