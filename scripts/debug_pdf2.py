"""Debug the PDF table structure."""
import sys
sys.path.insert(0, 'backend')

from app.services.pdf_import.extractors.pdfplumber_extractor import PdfplumberExtractor
from app.services.pdf_import.detectors.bank_detector import SignatureBankDetector
from app.services.pdf_import.parsers.factory import get_pdf_parser

file_path = "backend/uploads/493ef62b-2aed-43ce-aae4-937b18d77b09.pdf"
password = "192292"

extractor = PdfplumberExtractor()
extracted = extractor.extract(file_path, password=password)

print(f"Tables: {len(extracted.tables)}")
for i, table in enumerate(extracted.tables):
    print(f"\n=== TABLE {i} ({len(table)} rows) ===")
    for j, row in enumerate(table):
        print(f"  Row {j}: {row}")

print("\n\n=== ALL TEXT ===")
print(extracted.text)
