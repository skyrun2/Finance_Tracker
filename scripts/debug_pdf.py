"""Debug the pending PDF to see why no items were extracted."""
import sys
sys.path.insert(0, 'backend')

from app.services.pdf_import.extractors.pdfplumber_extractor import PdfplumberExtractor
from app.services.pdf_import.detectors.bank_detector import SignatureBankDetector
from app.services.pdf_import.parsers.factory import get_pdf_parser

file_path = "backend/uploads/493ef62b-2aed-43ce-aae4-937b18d77b09.pdf"
password = "192292"

extractor = PdfplumberExtractor()
extracted = extractor.extract(file_path, password=password)

print(f"Text length: {len(extracted.text)}")
print(f"Pages: {extracted.pages}")
print(f"Tables: {len(extracted.tables)}")
print("\n=== FIRST 1000 CHARS OF TEXT ===")
print(extracted.text[:1000])

detector = SignatureBankDetector()
bank = detector.detect(extracted.text)
print(f"\nBank detected: {bank.bank_code} / {bank.bank_name}")

parser = get_pdf_parser(bank.bank_code)
invoice = parser.parse(extracted)
print(f"\nInvoice items: {len(invoice.items)}")
for item in invoice.items:
    print(f"  {item.description[:50]:50s} | {item.amount:>8} | cat_hint={item.category_hint}")
print(f"Warnings: {invoice.warnings}")
