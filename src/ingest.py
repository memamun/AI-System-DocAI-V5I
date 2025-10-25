"""
Document Processor for AI-System-DocAI V5I
Handles document ingestion and preprocessing
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import logging

from loaders import load_file, iter_files

logger = logging.getLogger(__name__)

def _hash(s: str) -> str:
    """Generate SHA1 hash of a string"""
    return hashlib.sha1(s.encode()).hexdigest()

class DocumentProcessor:
    """Processes documents for indexing"""
    
    def __init__(self):
        pass
    
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single document
        
        Args:
            file_path: Path to the document file
        
        Returns:
            Dictionary containing document data:
            - text: Full text content
            - file_path: Path to the file
            - file_name: Name of the file
            - hash: Document hash
            - pages: List of pages (if applicable)
        """
        try:
            # Load document using loaders
            pages = load_file(file_path)
            
            if not pages:
                logger.warning(f"No content extracted from {file_path}")
                return None
            
            # Combine pages into full text
            full_text = "\n\n".join(pages)
            
            # Generate document hash based on path and modification time
            doc_hash = _hash(f"{file_path}|{int(file_path.stat().st_mtime)}")
            
            return {
                "text": full_text,
                "file_path": str(file_path.resolve()),
                "file_name": file_path.name,
                "hash": doc_hash,
                "pages": pages,
                "num_pages": len(pages)
            }
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {e}")
            return None
    
    def process_folder(self, folder_path: Path) -> List[Dict[str, Any]]:
        """
        Process all documents in a folder
        
        Args:
            folder_path: Path to the folder containing documents
        
        Returns:
            List of document data dictionaries
        """
        documents = []
        
        try:
            for file_path in iter_files(folder_path):
                doc = self.process_document(file_path)
                if doc:
                    documents.append(doc)
            
            logger.info(f"Processed {len(documents)} documents from {folder_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to process folder {folder_path}: {e}")
            return []

