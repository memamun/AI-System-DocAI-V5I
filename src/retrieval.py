# retrieval.py
from __future__ import annotations
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, field

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from config import DEFAULTS

@dataclass
class DocumentSnippet:
    """Represents a document snippet with metadata"""
    text: str
    file: str
    page: int = None
    section: str = None
    start_char: int = None
    end_char: int = None
    score: float = field(default=0.0)
    rank: int = field(default=0)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "file": self.file,
            "page": self.page,
            "section": self.section,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "score": self.score,
            "rank": self.rank
        }

class Retriever:
    """Hybrid retrieval system using FAISS + BM25 (CPU-only)"""
    
    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.idx = faiss.read_index(str(index_dir / "index.faiss"))
        self.metas: List[dict] = []
        with open(index_dir / "meta.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                self.metas.append(json.loads(line))
        info = json.loads((index_dir / "index.json").read_text(encoding="utf-8"))
        self.embed_model = info.get("embed_model", DEFAULTS["embed_model"])
        
        # Force CPU-only for embeddings
        self.embed = SentenceTransformer(self.embed_model, device="cpu")

        self.bm25 = None
        if DEFAULTS["bm25"]:
            corpus = [(m.get("text") or "") for m in self.metas]
            tokenized = [c.lower().split() for c in corpus]
            self.bm25 = BM25Okapi(tokenized)

    def search(self, q: str, k: int = DEFAULTS["k"]) -> List[Tuple[int, float]]:
        """
        Search for relevant documents using hybrid retrieval
        
        Args:
            q: Query string
            k: Number of results to return
        
        Returns:
            List of (index_id, score) tuples
        """
        # Dense retrieval (FAISS)
        qv = self.embed.encode([f"query: {q}"], normalize_embeddings=True, show_progress_bar=False).astype("float32")
        D, I = self.idx.search(qv, k)
        hits = list(zip(I[0].tolist(), D[0].tolist()))

        # Hybrid retrieval (BM25 + FAISS)
        if self.bm25 is not None:
            tok = q.lower().split()
            scores = self.bm25.get_scores(tok)
            s_min = float(np.min(scores))
            s_max = float(np.max(scores)) if float(np.max(scores)) != 0 else 1.0
            if s_max - s_min > 1e-9:
                scores = (scores - s_min) / (s_max - s_min)
            mix: Dict[int, float] = {}
            for idx_id, d in hits:
                mix[idx_id] = mix.get(idx_id, 0) + 0.6 * d
            top_sparse = np.argsort(scores)[-k:][::-1]
            for idx_id in top_sparse:
                mix[idx_id] = mix.get(idx_id, 0) + 0.4 * float(scores[idx_id])
            hits = sorted(mix.items(), key=lambda x: x[1], reverse=True)[:k]
        return hits

    def gather(self, hits: List[Tuple[int, float]]) -> List[Dict]:
        """
        Gather metadata for hit results
        
        Args:
            hits: List of (index_id, score) tuples
        
        Returns:
            List of metadata dictionaries with rank and score
        """
        out = []
        for rank, (idx_id, score) in enumerate(hits, start=1):
            m = self.metas[idx_id]
            m = {**m, "rank": rank, "score": float(score)}
            out.append(m)
        return out

    def format_context(self, passages: List[Dict]) -> str:
        """
        Format passages into readable context string
        
        Args:
            passages: List of passage metadata dictionaries
        
        Returns:
            Formatted context string
        """
        lines = []
        for p in passages:
            src = os.path.basename(p.get("file", "?"))
            pg = p.get("page", "?")
            txt = (p.get("text") or "").replace("\n", " ")
            lines.append(f"[{p['rank']}] {src} / page {pg} • score={p['score']:.3f}\n{txt}")
        return "\n\n".join(lines)

    def best_score(self, hits: List[Tuple[int, float]]) -> float:
        """Get the best score from hits"""
        return max([s for _, s in hits], default=0.0)

