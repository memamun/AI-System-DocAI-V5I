#!/usr/bin/env python3
"""
Index Manager for RAG System
Handles creation, deletion, rebuilding, and management of FAISS indexes
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import time

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from config import config_manager
from embeddings import EmbeddingManager
from ingest import DocumentProcessor

logger = logging.getLogger(__name__)

@dataclass
class IndexInfo:
    """Information about an index"""
    name: str
    path: str
    created_at: str
    last_modified: str
    document_count: int
    vector_count: int
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    documents: List[str]
    size_mb: float

class IndexManager:
    """Manages FAISS indexes for the RAG system"""
    
    def __init__(self):
        self.config = config_manager
        self.index_dir = Path(self.config.get_index_path())
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.embedding_manager = EmbeddingManager()
        self.document_processor = DocumentProcessor()
        # Note: Retriever will be initialized when needed with specific index directory
        
        # Index metadata file
        self.metadata_file = self.index_dir / "index_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load index metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load index metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save index metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save index metadata: {e}")
    
    def list_indexes(self) -> List[IndexInfo]:
        """List all available indexes"""
        indexes = []
        
        if not self.index_dir.exists():
            return indexes
        
        # Check for new-style indexes (in subdirectories)
        for index_path in self.index_dir.iterdir():
            if index_path.is_dir() and (index_path / "index.faiss").exists():
                try:
                    # Check if this is an old-style index (no metadata)
                    if index_path.name not in self.metadata:
                        self._create_metadata_for_existing_index(index_path.name)
                    
                    index_info = self._get_index_info(index_path.name)
                    if index_info:
                        indexes.append(index_info)
                except Exception as e:
                    logger.warning(f"Failed to get info for index {index_path.name}: {e}")
        
        # Check for old-style indexes (direct files in index directory)
        old_style_index = self.index_dir / "index.faiss"
        if old_style_index.exists():
            # If metadata doesn't exist, create it
            if "default_index" not in self.metadata:
                try:
                    self._create_metadata_for_old_style_index()
                except Exception as e:
                    logger.warning(f"Failed to create metadata for old-style index: {e}")
            
            # Add the index to the list if metadata exists
            if "default_index" in self.metadata:
                try:
                    index_info = self._get_index_info("default_index")
                    if index_info:
                        indexes.append(index_info)
                except Exception as e:
                    logger.warning(f"Failed to get info for old-style index: {e}")
        
        return sorted(indexes, key=lambda x: x.last_modified, reverse=True)
    
    def _create_metadata_for_existing_index(self, index_name: str):
        """Create metadata for an existing index that doesn't have it"""
        try:
            index_path = self.index_dir / index_name
            
            # Get file modification time
            faiss_file = index_path / "index.faiss"
            if faiss_file.exists():
                mod_time = time.ctime(faiss_file.stat().st_mtime)
            else:
                mod_time = "Unknown"
            
            # Count documents
            docs_dir = index_path / "documents"
            document_count = 0
            if docs_dir.exists():
                document_count = len(list(docs_dir.glob("*.txt")))
            
            # Try to get vector count from FAISS index
            vector_count = 0
            if FAISS_AVAILABLE and faiss_file.exists():
                try:
                    index = faiss.read_index(str(faiss_file))
                    vector_count = index.ntotal
                except:
                    pass
            
            # Create metadata
            self.metadata[index_name] = {
                'created_at': mod_time,
                'last_modified': mod_time,
                'document_count': document_count,
                'vector_count': vector_count,
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',  # Default
                'chunk_size': 800,  # Default
                'chunk_overlap': 120,  # Default
                'documents': [],  # Will be populated if we can find them
                'source_paths': []
            }
            
            # Save the metadata
            self._save_metadata()
            logger.info(f"Created metadata for existing index: {index_name}")
            
        except Exception as e:
            logger.error(f"Failed to create metadata for index {index_name}: {e}")
    
    def _create_metadata_for_old_style_index(self):
        """Create metadata for an old-style index (direct files in index directory)"""
        try:
            # Get file modification time
            faiss_file = self.index_dir / "index.faiss"
            if faiss_file.exists():
                mod_time = time.ctime(faiss_file.stat().st_mtime)
            else:
                mod_time = "Unknown"
            
            # Try to get vector count from FAISS index
            vector_count = 0
            if FAISS_AVAILABLE and faiss_file.exists():
                try:
                    index = faiss.read_index(str(faiss_file))
                    vector_count = index.ntotal
                except:
                    pass
            
            # Try to get document count from meta.jsonl
            document_count = 0
            meta_file = self.index_dir / "meta.jsonl"
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Count unique documents
                        unique_docs = set()
                        for line in lines:
                            if line.strip():
                                import json
                                meta = json.loads(line)
                                if 'file' in meta:
                                    unique_docs.add(meta['file'])
                        document_count = len(unique_docs)
                except:
                    pass
            
            # Create metadata for the old-style index
            self.metadata["default_index"] = {
                'created_at': mod_time,
                'last_modified': mod_time,
                'document_count': document_count,
                'vector_count': vector_count,
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',  # Default
                'chunk_size': 800,  # Default
                'chunk_overlap': 120,  # Default
                'documents': [],  # Will be populated if we can find them
                'source_paths': [],
                'is_old_style': True  # Mark as old-style index
            }
            
            # Save the metadata
            self._save_metadata()
            logger.info(f"Created metadata for old-style index: default_index")
            
        except Exception as e:
            logger.error(f"Failed to create metadata for old-style index: {e}")
    
    def _get_index_info(self, index_name: str) -> Optional[IndexInfo]:
        """Get information about a specific index"""
        # Get metadata
        metadata = self.metadata.get(index_name, {})
        
        # Handle old-style indexes (direct files in index directory)
        if metadata.get('is_old_style', False):
            return self._get_old_style_index_info(metadata)
        
        # Handle new-style indexes (in subdirectories)
        index_path = self.index_dir / index_name
        
        if not index_path.exists():
            return None
        
        # Get file sizes
        faiss_file = index_path / "index.faiss"
        pkl_file = index_path / "index.pkl"
        
        size_mb = 0
        if faiss_file.exists():
            size_mb += faiss_file.stat().st_size / (1024 * 1024)
        if pkl_file.exists():
            size_mb += pkl_file.stat().st_size / (1024 * 1024)
        
        # Get document count from metadata or count files
        document_count = metadata.get('document_count', 0)
        if document_count == 0:
            docs_dir = index_path / "documents"
            if docs_dir.exists():
                document_count = len(list(docs_dir.glob("*.txt")))
        
        return IndexInfo(
            name=index_name,
            path=str(index_path),
            created_at=metadata.get('created_at', 'Unknown'),
            last_modified=metadata.get('last_modified', 'Unknown'),
            document_count=document_count,
            vector_count=metadata.get('vector_count', 0),
            embedding_model=metadata.get('embedding_model', 'Unknown'),
            chunk_size=metadata.get('chunk_size', 1000),
            chunk_overlap=metadata.get('chunk_overlap', 200),
            documents=metadata.get('documents', []),
            size_mb=round(size_mb, 2)
        )
    
    def _get_old_style_index_info(self, metadata: dict) -> IndexInfo:
        """Get information for old-style index (direct files in index directory)"""
        # Calculate size of old-style index files
        size_mb = 0
        faiss_file = self.index_dir / "index.faiss"
        meta_file = self.index_dir / "meta.jsonl"
        info_file = self.index_dir / "index.json"
        
        if faiss_file.exists():
            size_mb += faiss_file.stat().st_size / (1024 * 1024)
        if meta_file.exists():
            size_mb += meta_file.stat().st_size / (1024 * 1024)
        if info_file.exists():
            size_mb += info_file.stat().st_size / (1024 * 1024)
        
        return IndexInfo(
            name="default_index",
            path=str(self.index_dir),
            created_at=metadata.get('created_at', 'Unknown'),
            last_modified=metadata.get('last_modified', 'Unknown'),
            document_count=metadata.get('document_count', 0),
            vector_count=metadata.get('vector_count', 0),
            embedding_model=metadata.get('embedding_model', 'Unknown'),
            chunk_size=metadata.get('chunk_size', 1000),
            chunk_overlap=metadata.get('chunk_overlap', 200),
            documents=metadata.get('documents', []),
            size_mb=round(size_mb, 2)
        )
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index and all its associated files"""
        try:
            # Handle old-style index (direct files in index directory)
            if index_name == "default_index" and (self.index_dir / "index.faiss").exists():
                # Delete old-style index files
                files_to_delete = ["index.faiss", "index.pkl", "index.json", "meta.jsonl", "index_metadata.json"]
                deleted_any = False
                for file_name in files_to_delete:
                    file_path = self.index_dir / file_name
                    if file_path.exists():
                        file_path.unlink()
                        deleted_any = True
                        logger.info(f"Deleted {file_name}")
                
                if deleted_any:
                    # Remove from metadata
                    if index_name in self.metadata:
                        del self.metadata[index_name]
                        self._save_metadata()
                    logger.info(f"Successfully deleted old-style index: {index_name}")
                    return True
                else:
                    logger.warning(f"No files found for old-style index: {index_name}")
                    return False
            
            # Handle new-style index (in subdirectory)
            index_path = self.index_dir / index_name
            
            if not index_path.exists():
                logger.warning(f"Index {index_name} does not exist")
                return False
            
            # Remove the entire index directory
            shutil.rmtree(index_path)
            
            # Remove from metadata
            if index_name in self.metadata:
                del self.metadata[index_name]
                self._save_metadata()
            
            logger.info(f"Successfully deleted index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False
    
    def delete_all_indexes(self) -> bool:
        """Delete all indexes"""
        try:
            indexes = self.list_indexes()
            if not indexes:
                logger.info("No indexes to delete")
                return True
            
            success_count = 0
            for index in indexes:
                if self.delete_index(index.name):
                    success_count += 1
            
            logger.info(f"Deleted {success_count}/{len(indexes)} indexes")
            return success_count == len(indexes)
            
        except Exception as e:
            logger.error(f"Failed to delete all indexes: {e}")
            return False
    
    def rebuild_index(self, index_name: str, source_documents: List[str]) -> bool:
        """Rebuild an index from source documents"""
        try:
            logger.info(f"Rebuilding index: {index_name}")
            
            # Delete existing index if it exists
            if self.index_exists(index_name):
                self.delete_index(index_name)
            
            # Create new index
            return self.create_index(index_name, source_documents)
            
        except Exception as e:
            logger.error(f"Failed to rebuild index {index_name}: {e}")
            return False
    
    def create_index(self, index_name: str, source_documents: List[str]) -> bool:
        """Create a new index from source documents"""
        try:
            logger.info(f"Creating index: {index_name} with {len(source_documents)} documents")
            
            # Create index directory
            index_path = self.index_dir / index_name
            index_path.mkdir(parents=True, exist_ok=True)
            
            # Process documents
            documents = []
            for doc_path in source_documents:
                if os.path.exists(doc_path):
                    doc_content = self.document_processor.process_document(Path(doc_path))
                    if doc_content and doc_content.get('text'):
                        documents.append(doc_content)
                else:
                    logger.warning(f"Document not found: {doc_path}")
            
            if not documents:
                logger.error("No valid documents found")
                return False
            
            # Create chunks (similar to indexer.py)
            all_chunks = []
            CHUNK_SIZE = 800
            CHUNK_OVERLAP = 120
            
            for doc in documents:
                text = doc['text']
                file_path = doc['file_path']
                doc_id = doc['hash']
                
                # Split text into chunks
                n = len(text)
                j = 0
                while j < n:
                    k = min(j + CHUNK_SIZE, n)
                    chunk_text = text[j:k].strip()
                    if chunk_text:
                        chunk = {
                            "text": chunk_text,
                            "file": file_path,
                            "page": 0,  # DocumentProcessor doesn't provide page info
                            "doc_id": doc_id,
                            "source": doc['file_name']
                        }
                        all_chunks.append(chunk)
                    
                    # Move to next chunk with overlap
                    if k >= n:
                        j = n
                    else:
                        next_j = k - min(CHUNK_OVERLAP, CHUNK_SIZE // 2)
                        j = next_j if next_j > j else k
            
            if not all_chunks:
                logger.error("No chunks created from documents")
                return False
            
            # Generate embeddings
            embeddings = self.embedding_manager.embed_texts([chunk['text'] for chunk in all_chunks])
            
            if embeddings is None or len(embeddings) == 0:
                logger.error("Failed to generate embeddings")
                return False
            
            # Create FAISS index
            if not FAISS_AVAILABLE:
                logger.error("FAISS not available")
                return False
            
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            index.add(embeddings)
            
            # Save index
            faiss.write_index(index, str(index_path / "index.faiss"))
            
            # Save chunks metadata
            import pickle
            with open(index_path / "index.pkl", 'wb') as f:
                pickle.dump(all_chunks, f)
            
            # Save documents
            docs_dir = index_path / "documents"
            docs_dir.mkdir(exist_ok=True)
            
            for i, doc in enumerate(documents):
                doc_file = docs_dir / f"document_{i}.txt"
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(doc['text'])
            
            # Update metadata
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.metadata[index_name] = {
                'created_at': current_time,
                'last_modified': current_time,
                'document_count': len(documents),
                'vector_count': len(all_chunks),
                'embedding_model': self.embedding_manager.model_name,
                'chunk_size': self.config.config.retrieval.chunk_size,
                'chunk_overlap': self.config.config.retrieval.chunk_overlap,
                'documents': source_documents,
                'source_paths': [doc['file_path'] for doc in documents]
            }
            self._save_metadata()
            
            logger.info(f"Successfully created index: {index_name} with {len(all_chunks)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    def index_exists(self, index_name: str) -> bool:
        """Check if an index exists"""
        # Check for new-style index (in subdirectory)
        index_path = self.index_dir / index_name
        if index_path.exists() and (index_path / "index.faiss").exists():
            return True
        
        # Check for old-style index (direct files in index directory)
        if index_name == "default_index":
            old_style_faiss = self.index_dir / "index.faiss"
            return old_style_faiss.exists()
        
        return False
    
    def get_index_status(self, index_name: str) -> Dict[str, Any]:
        """Get detailed status of an index"""
        try:
            if not self.index_exists(index_name):
                return {
                    'exists': False,
                    'error': 'Index does not exist'
                }
            
            # Load FAISS index
            if not FAISS_AVAILABLE:
                return {
                    'exists': True,
                    'error': 'FAISS not available'
                }
            
            # Determine the FAISS file path (new-style vs old-style)
            if index_name == "default_index" and (self.index_dir / "index.faiss").exists():
                # Old-style index
                faiss_file = self.index_dir / "index.faiss"
                pkl_file = self.index_dir / "index.pkl"
            else:
                # New-style index
                index_path = self.index_dir / index_name
                faiss_file = index_path / "index.faiss"
                pkl_file = index_path / "index.pkl"
            
            index = faiss.read_index(str(faiss_file))
            
            # Load chunks
            chunks = []
            if pkl_file.exists():
                import pickle
                with open(pkl_file, 'rb') as f:
                    chunks = pickle.load(f)
            
            # Get metadata
            metadata = self.metadata.get(index_name, {})
            
            return {
                'exists': True,
                'vector_count': index.ntotal,
                'dimension': index.d,
                'chunk_count': len(chunks),
                'document_count': metadata.get('document_count', 0),
                'embedding_model': metadata.get('embedding_model', 'Unknown'),
                'created_at': metadata.get('created_at', 'Unknown'),
                'last_modified': metadata.get('last_modified', 'Unknown'),
                'size_mb': self._get_index_size(index_name),
                'is_valid': len(chunks) == index.ntotal if chunks else True  # Valid if no chunks to compare
            }
            
        except Exception as e:
            logger.error(f"Failed to get index status for {index_name}: {e}")
            return {
                'exists': True,
                'error': str(e)
            }
    
    def _get_index_size(self, index_name: str) -> float:
        """Get the size of an index in MB"""
        try:
            # Handle old-style index
            if index_name == "default_index" and (self.index_dir / "index.faiss").exists():
                total_size = 0
                for file_name in ["index.faiss", "index.pkl", "index.json", "meta.jsonl", "index_metadata.json"]:
                    file_path = self.index_dir / file_name
                    if file_path.exists():
                        total_size += file_path.stat().st_size
                return round(total_size / (1024 * 1024), 2)
            
            # Handle new-style index
            index_path = self.index_dir / index_name
            total_size = 0
            
            for file_path in index_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def validate_index(self, index_name: str) -> bool:
        """Validate that an index is working correctly"""
        try:
            status = self.get_index_status(index_name)
            
            if not status.get('exists', False):
                return False
            
            if 'error' in status:
                return False
            
            # Check if vector count matches chunk count
            if not status.get('is_valid', False):
                return False
            
            # Try to load the retrieval manager with this index
            try:
                # This is a basic validation - in practice you'd want more thorough testing
                return True
            except Exception:
                return False
                
        except Exception as e:
            logger.error(f"Failed to validate index {index_name}: {e}")
            return False
    
    def get_index_summary(self) -> Dict[str, Any]:
        """Get a summary of all indexes"""
        indexes = self.list_indexes()
        
        total_indexes = len(indexes)
        total_vectors = sum(index.vector_count for index in indexes)
        total_documents = sum(index.document_count for index in indexes)
        total_size = sum(index.size_mb for index in indexes)
        
        return {
            'total_indexes': total_indexes,
            'total_vectors': total_vectors,
            'total_documents': total_documents,
            'total_size_mb': round(total_size, 2),
            'indexes': [
                {
                    'name': idx.name,
                    'vectors': idx.vector_count,
                    'documents': idx.document_count,
                    'size_mb': idx.size_mb,
                    'created': idx.created_at,
                    'model': idx.embedding_model
                }
                for idx in indexes
            ]
        }
    
    def cleanup_orphaned_indexes(self) -> int:
        """Remove indexes that are no longer valid or have missing files"""
        try:
            indexes = self.list_indexes()
            removed_count = 0
            
            for index in indexes:
                if not self.validate_index(index.name):
                    logger.info(f"Removing orphaned index: {index.name}")
                    if self.delete_index(index.name):
                        removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} orphaned indexes")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned indexes: {e}")
            return 0
    
    def rename_index(self, old_name: str, new_name: str) -> bool:
        """Rename an index"""
        try:
            if not self.index_exists(old_name):
                logger.warning(f"Index {old_name} does not exist")
                return False
            
            if self.index_exists(new_name):
                logger.warning(f"Index {new_name} already exists")
                return False
            
            # Handle old-style index (direct files in index directory)
            if old_name == "default_index" and (self.index_dir / "index.faiss").exists():
                # For old-style indexes, we can't easily rename the files
                # Instead, we'll create new-style index with the new name
                logger.info(f"Converting old-style index {old_name} to new-style index {new_name}")
                
                # Get the old metadata
                old_metadata = self.metadata.get(old_name, {})
                
                # Create new index directory
                new_index_path = self.index_dir / new_name
                new_index_path.mkdir(exist_ok=True)
                
                # Copy files to new location
                files_to_copy = ["index.faiss", "index.pkl", "index.json", "meta.jsonl", "index_metadata.json"]
                for file_name in files_to_copy:
                    old_file = self.index_dir / file_name
                    if old_file.exists():
                        new_file = new_index_path / file_name
                        shutil.copy2(old_file, new_file)
                
                # Copy documents directory if it exists
                old_docs_dir = self.index_dir / "documents"
                if old_docs_dir.exists():
                    new_docs_dir = new_index_path / "documents"
                    shutil.copytree(old_docs_dir, new_docs_dir)
                
                # Update metadata
                new_metadata = old_metadata.copy()
                new_metadata['created_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                new_metadata['last_modified'] = time.strftime("%Y-%m-%d %H:%M:%S")
                new_metadata['is_old_style'] = False  # Now it's new-style
                
                self.metadata[new_name] = new_metadata
                
                # Remove old metadata
                if old_name in self.metadata:
                    del self.metadata[old_name]
                
                # Delete old files
                for file_name in files_to_copy:
                    old_file = self.index_dir / file_name
                    if old_file.exists():
                        old_file.unlink()
                
                if old_docs_dir.exists():
                    shutil.rmtree(old_docs_dir)
                
                self._save_metadata()
                logger.info(f"Successfully renamed index from {old_name} to {new_name}")
                return True
            
            # Handle new-style index (in subdirectory)
            old_index_path = self.index_dir / old_name
            new_index_path = self.index_dir / new_name
            
            if not old_index_path.exists():
                logger.warning(f"Index {old_name} does not exist")
                return False
            
            # Move the directory
            shutil.move(str(old_index_path), str(new_index_path))
            
            # Update metadata
            if old_name in self.metadata:
                old_metadata = self.metadata[old_name]
                new_metadata = old_metadata.copy()
                new_metadata['last_modified'] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                self.metadata[new_name] = new_metadata
                del self.metadata[old_name]
                self._save_metadata()
            
            logger.info(f"Successfully renamed index from {old_name} to {new_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rename index from {old_name} to {new_name}: {e}")
            return False
