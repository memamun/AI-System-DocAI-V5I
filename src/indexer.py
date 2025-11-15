# indexer.py
from __future__ import annotations
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import json, gc, hashlib
from dataclasses import asdict
from pathlib import Path
from typing import List, Callable, Tuple, Dict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from loaders import iter_files, load_file
from config import IndexConfig
from chunking import ContextualChunker, smart_chunk_text

PERSIST_EVERY = 2000
BATCH_SIZE = int(os.getenv("RAG_EMB_BATCH", "8"))

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()

def _create_index(dim: int, index_type: str, num_vectors: int = 0) -> faiss.Index:
    """Create a FAISS index of the specified type"""
    if index_type == "flat":
        return faiss.IndexFlatIP(dim)
    if index_type == "hnsw":
        idx = faiss.IndexHNSWFlat(dim, 32)
        idx.hnsw.efConstruction = 80
        idx.hnsw.efSearch = 64
        return idx
    if index_type == "ivf":
        # Adjust nlist based on the number of vectors if known
        if num_vectors > 0:
            nlist = min(1024, 4 * round(num_vectors**0.5))
        else:
            nlist = 1024
        
        # Ensure nlist is at least 1
        nlist = max(1, nlist)

        quantizer = faiss.IndexFlatIP(dim)
        return faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
    raise ValueError("unknown index type")

class Indexer:
    """Document indexer with CPU-only embeddings and FAISS"""
    
    def __init__(
        self,
        out_dir: Path,
        cfg: IndexConfig,
        on_status: Callable[[str], None] = lambda s: None,
        on_progress: Callable[[int], None] = lambda p: None,
        should_cancel: Callable[[], bool] = lambda: False,
    ):
        self.out_dir = out_dir
        self.cfg = cfg
        self.on_status = on_status
        self.on_progress = on_progress
        self.should_cancel = should_cancel

        self.meta_path = self.out_dir / "meta.jsonl"
        self.idx_path = self.out_dir / "index.faiss"
        self.info_path = self.out_dir / "index.json"
        
        # Initialize intelligent chunker
        self.chunker = ContextualChunker(
            chunk_size=1000,  # Increased from 800 for better context
            overlap=200,      # Increased from 120 for more overlap
            min_chunk_size=100
        )
        
        # Buffer for IVF training
        self._ivf_training_buffer: List[np.ndarray] = []
        self._ivf_meta_buffer: List[dict] = []

    def _save_info(self):
        """Save index configuration to JSON file"""
        self.info_path.write_text(
            json.dumps(asdict(self.cfg), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def build(self, folder: Path) -> Tuple[int, int]:
        """
        Build the index from documents in the given folder
        
        Args:
            folder: Path to folder containing documents
        
        Returns:
            Tuple of (processed_files, total_vectors)
        """
        os.makedirs(self.out_dir, exist_ok=True)
        if self.idx_path.exists(): self.idx_path.unlink()
        if self.meta_path.exists(): self.meta_path.unlink()

        # Force CPU-only
        device = "cpu"

        # Set environment variables for this process too
        cache_dir = self.out_dir.parent / "cache" / "transformers"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
        os.environ["HF_HOME"] = str(cache_dir)
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir)

        # Pre-download and load embedding model with retry logic
        self.on_status(f"Preparing embedding model '{self.cfg.embed_model}' on {device}…")

        # Import the improved embedding loader
        from embeddings import ensure_model_available, load_embedding_model

        # First ensure model is available (pre-download if needed)
        if not ensure_model_available(self.cfg.embed_model):
            self.on_status(f"Warning: Could not pre-download {self.cfg.embed_model}. Will try to load during indexing.")

        # Try to load from local cache first
        local_model_path = cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
        if local_model_path.exists():
            import glob
            model_dirs = glob.glob(str(local_model_path / "*"))
            if model_dirs:
                actual_model_path = model_dirs[0]
                self.on_status(f"Loading model from local cache: {self.cfg.embed_model}")
                try:
                    emb = SentenceTransformer(actual_model_path, device="cpu", trust_remote_code=False)
                    self.on_status(f"Embedder: {self.cfg.embed_model} ready (CPU)")
                except Exception as e:
                    self.on_status(f"Error loading from cache, falling back to online: {e}")
                    emb = load_embedding_model(self.cfg.embed_model)
            else:
                emb = load_embedding_model(self.cfg.embed_model)
        else:
            # Load the embedding model with retry logic
            emb = load_embedding_model(self.cfg.embed_model)

        self.on_status(f"Embedder: {self.cfg.embed_model} ready (CPU)")

        files = list(iter_files(folder))
        total_files = len(files)
        if not total_files:
            self.on_status("No supported files found.")
            return (0, 0)

        meta_f = open(self.meta_path, "w", encoding="utf-8")
        index = None
        total_vecs = 0
        processed = 0

        def add_texts(texts: List[str], metas: List[dict]):
            nonlocal index, total_vecs
            if not texts: return
            inputs = texts
            for start in range(0, len(inputs), BATCH_SIZE):
                batch_inputs = inputs[start:start+BATCH_SIZE]
                batch_metas  = metas[start:start+BATCH_SIZE]
                vecs = emb.encode(batch_inputs, normalize_embeddings=True, show_progress_bar=False)
                vecs = vecs.astype("float32")
                
                if index is None:
                    # For IVF, we might need to wait for more vectors to train, so don't create it yet
                    if self.cfg.index_type != "ivf":
                        index = _create_index(vecs.shape[1], self.cfg.index_type)

                # Special handling for IVF index training
                if self.cfg.index_type == "ivf":
                    if vecs.shape[0] > 0:
                        self._ivf_training_buffer.append(vecs)
                        self._ivf_meta_buffer.extend(batch_metas)
                    # Don't add to index or write meta yet, buffer it
                    continue

                if vecs.shape[0] > 0:
                    index.add(vecs)
                    for m in batch_metas:
                        meta_f.write(json.dumps(m, ensure_ascii=False) + "\n")
                    meta_f.flush()
                    total_vecs += vecs.shape[0]
                    self.on_status(f"Embeddings: +{vecs.shape[0]} (total={total_vecs})")

                if total_vecs % PERSIST_EVERY == 0 and self.cfg.index_type != "ivf":
                    faiss.write_index(index, str(self.idx_path))
            gc.collect()

        for i, path in enumerate(files, start=1):
            if self.should_cancel():
                self.on_status("Cancelled by user."); break

            self.on_status(f"Indexing: {path.name}")
            try:
                pages = load_file(path)
            except Exception as e:
                self.on_status(f"[SKIP] {path.name}: {e}")
                continue

            chunks: List[str] = []
            metas: List[Dict] = []

            # for each extracted "page" (or text block) from the loader
            # pages can return either strings (backward compatibility) or (text, page_number) tuples
            for idx, item in enumerate(pages):
                # Handle both formats: strings or tuples
                if isinstance(item, tuple) and len(item) == 2:
                    text, page_num = item
                else:
                    # Backward compatibility: treat as string with page index
                    text = item
                    # Use enumerate index as page number (0-based internally)
                    page_num = idx
                
                # Use intelligent chunking to preserve semantic boundaries
                chunked_passages = self.chunker.chunk(
                    text, 
                    page_num,
                    metadata={
                        "file": str(path.resolve()),
                        "doc_id": _hash(f"{path}|{int(path.stat().st_mtime)}"),
                    }
                )
                
                # Process each intelligently chunked passage
                for passage in chunked_passages:
                    chunk_text = passage["text"]
                    if chunk_text.strip():
                        # Prepare metadata with structural information
                        chunk_meta = {
                            "file": passage.get("file", str(path.resolve())),
                            "page": passage.get("page", page_num),
                            "text": chunk_text,
                            "doc_id": passage.get("doc_id", _hash(f"{path}|{int(path.stat().st_mtime)}")),
                            "chunk_type": passage.get("chunk_type", "standard"),
                            "section": passage.get("section"),
                            "hierarchy": passage.get("hierarchy", 0),
                        }
                        
                        metas.append(chunk_meta)
                        chunks.append(chunk_text)
                        
                        # periodic flush
                        if len(chunks) >= 64:
                            add_texts(chunks, metas)
                            chunks, metas = [], []

            if chunks:
                add_texts(chunks, metas)

            processed += 1
            pct = int(processed * 100 / total_files)
            self.on_progress(pct)

        meta_f.close()
        
        # Finalize IVF index if used
        if self.cfg.index_type == "ivf" and self._ivf_training_buffer:
            self.on_status("Finalizing IVF index...")
            # Consolidate all vectors from buffer
            all_vecs = np.vstack(self._ivf_training_buffer)
            self._ivf_training_buffer = [] # Clear buffer
            dim = all_vecs.shape[1]
            num_vectors = all_vecs.shape[0]

            if num_vectors > 0:
                index = _create_index(dim, "ivf", num_vectors=num_vectors)
                
                # Train the index
                if index.nlist <= num_vectors:
                    self.on_status(f"Training IVF index with {num_vectors} vectors and nlist={index.nlist}...")
                    index.train(all_vecs)
                    self.on_status("IVF training complete.")
                else:
                    self.on_status(f"Warning: Not enough vectors ({num_vectors}) to train IVF with nlist={index.nlist}. Using Flat index as fallback.")
                    index = faiss.IndexFlatIP(dim)
                
                # Add all vectors to the now-trained index
                index.add(all_vecs)
                total_vecs = num_vectors
                self.on_status(f"Added {total_vecs} vectors to the IVF index.")

                # Now write the buffered metadata
                self.on_status("Writing metadata...")
                with open(self.meta_path, "w", encoding="utf-8") as meta_f:
                    for m in self._ivf_meta_buffer:
                        meta_f.write(json.dumps(m, ensure_ascii=False) + "\n")
                self._ivf_meta_buffer = [] # Clear buffer
                self.on_status("Metadata written.")

        if index is not None:
            faiss.write_index(index, str(self.idx_path))
        self._save_info()
        self.on_status(f"Done. Files: {processed}/{total_files} • Vectors: {total_vecs}")
        return (processed, total_vecs)

