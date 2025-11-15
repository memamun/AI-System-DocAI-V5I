# loaders.py
from __future__ import annotations
import os, re
from pathlib import Path
from typing import Iterable, List, Tuple

import chardet
import fitz  # PyMuPDF
from pypdf import PdfReader
import docx2txt
from pptx import Presentation
import pandas as pd

TEXT_EXTS = {".txt", ".md", ".csv"}
DOC_EXTS  = {".docx"}
PPT_EXTS  = {".pptx"}
XLS_EXTS  = {".xlsx"}
PDF_EXTS  = {".pdf"}
SUPPORTED = TEXT_EXTS | DOC_EXTS | PPT_EXTS | XLS_EXTS | PDF_EXTS

_ws = re.compile(r"[ \t\u00A0]+")

# Safety cap for huge PDFs
MAX_PDF_PAGES = int(os.getenv("RAG_MAX_PDF_PAGES", "200"))

def _clean(s: str) -> str:
    s = s.replace("\x00", " ")
    s = s.replace("\f", "\n\n")
    s = re.sub(r"\r\n?|\n", "\n", s)
    s = _ws.sub(" ", s)
    return s.strip()


def _segment_text(text: str, max_chars: int = 1800) -> List[str]:
    """Split long DOCX text into pseudo-pages to preserve citation locations."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if not paragraphs:
        return [text]

    segments: List[str] = []
    current: List[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current and current_len + para_len > max_chars:
            segments.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len

    if current:
        segments.append("\n\n".join(current))

    return segments or [text]

def from_text_like(path: Path) -> List[Tuple[str, int]]:
    """Extract text from plain text files"""
    raw = path.read_bytes()
    enc = chardet.detect(raw).get("encoding") or "utf-8"
    try:
        txt = raw.decode(enc, errors="ignore")
    except Exception:
        txt = raw.decode("utf-8", errors="ignore")
    cleaned = _clean(txt)
    # Text files don't have pages, use page 1 for the entire file
    return [(cleaned, 1)] if cleaned else []

def from_pdf_pymupdf(path: Path) -> List[Tuple[str, int]]:
    """Extract text from PDF with actual page numbers"""
    out: List[Tuple[str, int]] = []
    with fitz.open(str(path)) as doc:
        n = min(len(doc), MAX_PDF_PAGES)
        for i in range(n):
            t = doc[i].get_text("text") or ""
            if t.strip():
                # Use index + 1 as page number (most reliable - matches PDF viewer)
                # This is the simplest and most accurate approach
                page_num = i + 1
                out.append((_clean(t), page_num))
    return out

def from_pdf_pypdf(path: Path) -> List[Tuple[str, int]]:
    """Extract text from PDF with actual page numbers"""
    out: List[Tuple[str, int]] = []
    r = PdfReader(str(path))
    n = min(len(r.pages), MAX_PDF_PAGES)
    for i in range(n):
        t = (r.pages[i].extract_text() or "").strip()
        if t:
            # Use extraction index + 1 as page number
            page_num = i + 1
            out.append((_clean(t), page_num))
    return out

def from_pdf(path: Path) -> List[Tuple[str, int]]:
    # 1) try PyMuPDF (fast)
    try:
        return from_pdf_pymupdf(path)
    except Exception:
        pass
    # 2) fallback to pypdf (slower, but sometimes useful)
    try:
        return from_pdf_pypdf(path)
    except Exception:
        return []

def from_docx(path: Path) -> List[Tuple[str, int]]:
    """Extract text from DOCX with page tracking"""
    raw_text = docx2txt.process(str(path)) or ""
    if not raw_text:
        return []

    # Split on explicit page breaks when available (docx2txt marks them with form-feed)
    pieces = [piece for piece in raw_text.split("\f") if piece.strip()]

    if not pieces:
        return []

    # If no explicit page breaks were found, fall back to heuristic segmentation
    if len(pieces) == 1:
        pieces = _segment_text(pieces[0])

    cleaned: List[Tuple[str, int]] = []
    for idx, piece in enumerate(pieces):
        cleaned_piece = _clean(piece)
        if cleaned_piece:
            # Use 1-based page numbering to match PDF loaders
            page_num = idx + 1
            cleaned.append((cleaned_piece, page_num))

    return cleaned

def from_pptx(path: Path) -> List[Tuple[str, int]]:
    """Extract text from PPTX with slide tracking"""
    prs = Presentation(str(path))
    buf: List[Tuple[str, int]] = []
    for i, slide in enumerate(prs.slides, 1):
        parts = []
        for shp in slide.shapes:
            if hasattr(shp, "has_text_frame") and shp.has_text_frame:
                parts.append(shp.text)
        if parts:
            buf.append((_clean(f"Slide {i}: " + " \n ".join(parts)), i))
    return buf

def from_xlsx(path: Path, max_cells: int = 5000) -> List[Tuple[str, int]]:
    """Extract text from XLSX with sheet tracking"""
    dfs = pd.read_excel(str(path), sheet_name=None, dtype=str)
    out: List[Tuple[str, int]] = []
    cells = 0
    page_num = 1
    for name, df in dfs.items():
        df = df.fillna("")
        for _, row in df.iterrows():
            if cells > max_cells:
                break
            line = " | ".join(map(str, row.tolist()))
            if line.strip():
                out.append((_clean(f"{name}: {line}"), page_num))
                cells += len(row)
        if cells > max_cells:
            break
        page_num += 1
    return out

def load_file(path: Path) -> List[Tuple[str, int]]:
    """Load file and return list of (text, page_number) tuples"""
    ext = path.suffix.lower()
    if ext in PDF_EXTS:  return from_pdf(path)
    if ext in DOC_EXTS:  return from_docx(path)
    if ext in PPT_EXTS:  return from_pptx(path)
    if ext in XLS_EXTS:  return from_xlsx(path)
    if ext in TEXT_EXTS:
        # For text files, treat entire content as page 1
        result = from_text_like(path)
        return [(text, 1) for text in result]
    return []

def iter_files(folder: Path) -> Iterable[Path]:
    # Allow temporarily disabling PDFs for debugging:
    disable_pdf = os.getenv("RAG_DISABLE_PDF", "0") == "1"
    for p in folder.rglob("*"):
        if p.is_file():
            ext = p.suffix.lower()
            if disable_pdf and ext in PDF_EXTS:
                continue
            if ext in SUPPORTED:
                yield p

