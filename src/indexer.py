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

PERSIST_EVERY = 2000
BATCH_SIZE = int(os.getenv("RAG_EMB_BATCH", "8"))

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()

def _create_index(dim: int, index_type: str) -> faiss.Index:
    """Create a FAISS index of the specified type"""
    if index_type == "flat":
        return faiss.IndexFlatIP(dim)
    if index_type == "hnsw":
        idx = faiss.IndexHNSWFlat(dim, 32)
        idx.hnsw.efConstruction = 80
        idx.hnsw.efSearch = 64
        return idx
    if index_type == "ivf":
        quantizer = faiss.IndexFlatIP(dim)
        nlist = 1024
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
            inputs = [f"passage: {t}" for t in texts]
            for start in range(0, len(inputs), BATCH_SIZE):
                batch_inputs = inputs[start:start+BATCH_SIZE]
                batch_metas  = metas[start:start+BATCH_SIZE]
                vecs = emb.encode(batch_inputs, normalize_embeddings=True, show_progress_bar=False)
                vecs = vecs.astype("float32")
                if index is None:
                    index = _create_index(vecs.shape[1], self.cfg.index_type)
                    if isinstance(index, faiss.IndexIVF):
                        train_n = min(50000, vecs.shape[0])
                        index.train(vecs[:train_n])
                index.add(vecs)
                for m in batch_metas:
                    meta_f.write(json.dumps(m, ensure_ascii=False) + "\n")
                meta_f.flush()
                total_vecs += vecs.shape[0]
                self.on_status(f"Embeddings: +{vecs.shape[0]} (total={total_vecs})")
                if total_vecs % PERSIST_EVERY == 0:
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
            CHUNK = 800
            OVER  = 120

            # for each extracted "page" (or text block) from the loader
            for pg, text in enumerate(pages):
                n = len(text)
                j = 0
                while j < n:
                    k = min(j + CHUNK, n)
                    chunk = text[j:k].strip()
                    if chunk:
                        metas.append({
                            "file": str(path.resolve()),
                            "page": pg,
                            "text": chunk,
                            "doc_id": _hash(f"{path}|{int(path.stat().st_mtime)}"),
                        })
                        chunks.append(chunk)

                    # ensure progress always increases
                    if k >= n:
                        j = n
                    else:
                        next_j = k - min(OVER, CHUNK // 2)
                        j = next_j if next_j > j else k

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
        if index is not None:
            faiss.write_index(index, str(self.idx_path))
        self._save_info()
        self.on_status(f"Done. Files: {processed}/{total_files} • Vectors: {total_vecs}")
        return (processed, total_vecs)

