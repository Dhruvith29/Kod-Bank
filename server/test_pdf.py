import os
import traceback
import io
import pypdf
import re

# Mock the extraction logic exactly as it is in fundamental.py
def extract_text(file_bytes: bytes) -> list[dict]:
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    pages = []
    
    financial_keywords = [
        "balance sheet", "income statement", "statement of earnings",
        "cash flow statement", "statement of cash flows", "financial highlights",
        "key metrics", "consolidated statement", "risk factors",
        "management's discussion", "md&a"
    ]
    
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        
        if text:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in financial_keywords):
                pages.append({"page": i, "text": text})
                
    if not pages and len(reader.pages) > 0:
        for i, page in enumerate(reader.pages, start=1):
            if i <= 10 or i >= len(reader.pages) - 10:
                text = page.extract_text() or ""
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    pages.append({"page": i, "text": text})
                    
    return pages

# Create a mock PDF with one page of text
def create_mock_pdf() -> bytes:
    from reportlab.pdfgen import canvas
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "This is a mock balance sheet page.")
    c.showPage()
    c.save()
    return buffer.getvalue()

if __name__ == "__main__":
    try:
        pdf_bytes = create_mock_pdf()
        print("Mock PDF created.")
        pages = extract_text(pdf_bytes)
        print(f"Extracted {len(pages)} pages.")
    except Exception as e:
        print("Fatal error during extraction:")
        traceback.print_exc()
