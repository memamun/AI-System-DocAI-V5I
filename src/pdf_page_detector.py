"""
PDF Page Number Detector
Auto-detects the page offset needed for a PDF to match actual page numbers
"""
from pathlib import Path
import re
from typing import Optional, Tuple

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


def detect_pdf_page_offset(pdf_path: Path) -> Tuple[int, str]:
    """
    Auto-detect the page offset needed for a PDF
    
    Returns:
        Tuple of (offset, explanation)
        - offset: The page offset to use (0 for no offset, negative/positive for adjustment)
        - explanation: Human-readable explanation
        
    Example:
        offset, reason = detect_pdf_page_offset(Path("document.pdf"))
        # If offset is 0, use default: no adjustment needed
        # If offset is -13, subtract 13 from extracted pages
    """
    
    if not HAS_FITZ:
        return 0, "PyMuPDF not available - using default page numbers"
    
    if not pdf_path.exists():
        return 0, "PDF file not found"
    
    try:
        with fitz.open(str(pdf_path)) as doc:
            # Check first few pages for page label information
            page_labels = []
            for i in range(min(10, len(doc))):
                try:
                    label = doc.get_page_label(i)
                    if label:
                        # Extract numeric part
                        numeric_match = re.search(r'\d+', label)
                        if numeric_match:
                            page_num = int(numeric_match.group())
                            page_labels.append((i, page_num))
                except:
                    pass
            
            if page_labels:
                # Analyze the pattern
                first_index, first_label = page_labels[0]
                offset = first_label - (first_index + 1)
                
                if offset == 0:
                    return 0, "✓ No offset needed - PDF page numbers match display"
                elif offset > 0:
                    return offset, f"✓ PDF starts at page {first_label} (add {offset} to extracted pages)"
                else:
                    return offset, f"✓ PDF has front matter (~{abs(offset)} pages) - subtract {abs(offset)} from extracted pages"
            
            # No page labels detected - use default
            return 0, "No page labels found - using sequential page numbers"
            
    except Exception as e:
        return 0, f"Could not detect offset: {str(e)}"


def analyze_pdf(pdf_path: Path) -> dict:
    """
    Comprehensive PDF analysis for page numbering
    
    Returns:
        Dictionary with:
        - offset: Detected offset
        - reason: Explanation
        - total_pages: Total number of pages
        - has_labels: Whether PDF has page labels
        - sample_labels: Sample page labels from first 5 pages
    """
    
    result = {
        "offset": 0,
        "reason": "Unknown",
        "total_pages": 0,
        "has_labels": False,
        "sample_labels": []
    }
    
    if not HAS_FITZ:
        result["reason"] = "PyMuPDF not available"
        return result
    
    try:
        with fitz.open(str(pdf_path)) as doc:
            result["total_pages"] = len(doc)
            
            # Get sample labels
            for i in range(min(5, len(doc))):
                try:
                    label = doc.get_page_label(i)
                    if label:
                        result["has_labels"] = True
                        result["sample_labels"].append({
                            "extraction_index": i,
                            "page_label": label
                        })
                except:
                    pass
            
            # Detect offset
            offset, reason = detect_pdf_page_offset(pdf_path)
            result["offset"] = offset
            result["reason"] = reason
            
    except Exception as e:
        result["reason"] = f"Error analyzing PDF: {str(e)}"
    
    return result


def print_pdf_analysis(pdf_path: Path) -> None:
    """Pretty print PDF analysis"""
    print(f"\n{'='*60}")
    print(f"PDF Page Analysis: {pdf_path.name}")
    print(f"{'='*60}")
    
    analysis = analyze_pdf(pdf_path)
    
    print(f"Total Pages: {analysis['total_pages']}")
    print(f"Page Labels Found: {'Yes' if analysis['has_labels'] else 'No'}")
    print(f"\nPage Offset: {analysis['offset']}")
    print(f"Reason: {analysis['reason']}")
    
    if analysis['sample_labels']:
        print(f"\nSample Page Labels:")
        for sample in analysis['sample_labels']:
            print(f"  Position {sample['extraction_index'] + 1}: Label = '{sample['page_label']}'")
    
    print(f"\nConfiguration for config.py:")
    if analysis['offset'] == 0:
        print(f"  pdf_page_offset: 0  # No adjustment needed")
    else:
        print(f"  pdf_page_offset: {analysis['offset']}  # Adjust by {analysis['offset']}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_page_detector.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    print_pdf_analysis(pdf_path)

