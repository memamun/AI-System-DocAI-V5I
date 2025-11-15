"""
Test script to verify PDF page number detection
Run this to check if page numbers are being detected correctly
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loaders import from_pdf_pymupdf

def test_pdf_pages(pdf_path: str):
    """Test page number detection for a PDF"""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing PDF: {pdf_path.name}")
    print(f"{'='*60}\n")
    
    try:
        pages = from_pdf_pymupdf(pdf_path)
        
        print(f"Total pages extracted: {len(pages)}\n")
        print("First 10 pages:")
        print("-" * 60)
        for i, (text, page_num) in enumerate(pages[:10], 1):
            preview = text[:50].replace('\n', ' ') + "..."
            print(f"Index {i:2d} → Page {page_num:3d} | {preview}")
        
        print("\n" + "-" * 60)
        print("Last 5 pages:")
        print("-" * 60)
        for i, (text, page_num) in enumerate(pages[-5:], len(pages) - 4):
            preview = text[:50].replace('\n', ' ') + "..."
            print(f"Index {i:2d} → Page {page_num:3d} | {preview}")
        
        # Check for consistency
        print("\n" + "-" * 60)
        print("Page Number Analysis:")
        print("-" * 60)
        
        page_nums = [page_num for _, page_num in pages]
        min_page = min(page_nums)
        max_page = max(page_nums)
        
        print(f"Page range: {min_page} to {max_page}")
        print(f"Total pages: {len(pages)}")
        
        # Check if offset was detected
        first_page = page_nums[0] if page_nums else 1
        expected_first = 1
        offset = first_page - expected_first
        
        if offset == 0:
            print(f"✓ No offset detected - pages start at 1")
        elif offset > 0:
            print(f"✓ Offset detected: +{offset} (pages start at {first_page})")
        else:
            print(f"✓ Offset detected: {offset} (pages start at {first_page})")
        
        # Check for gaps or inconsistencies
        gaps = []
        for i in range(len(page_nums) - 1):
            if page_nums[i+1] - page_nums[i] > 1:
                gaps.append((i, page_nums[i], page_nums[i+1]))
        
        if gaps:
            print(f"\n⚠️  Warning: Found {len(gaps)} page number gaps:")
            for idx, p1, p2 in gaps[:5]:  # Show first 5
                print(f"   Gap at index {idx}: page {p1} → page {p2}")
        else:
            print("✓ No page number gaps detected")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_page_detection.py <pdf_path>")
        print("\nExample:")
        print("  python test_page_detection.py C:/Users/aamam/Downloads/test_db/ComputerNetworks.pdf")
        sys.exit(1)
    
    test_pdf_pages(sys.argv[1])


