"""Process the pending PDF import and confirm it."""
import asyncio
import sys
sys.path.insert(0, 'backend')

from app.database import async_session
from app.models import Import
from app.services.pdf_import.pdf_pipeline import process_pdf, confirm_import
from sqlalchemy import select
import uuid


async def main():
    import_id = "510b3b59-ec3a-496c-ae85-8028a45f116b"
    file_path = "backend/uploads/493ef62b-2aed-43ce-aae4-937b18d77b09.pdf"
    account_id = "bea45e7b-bba2-4cfe-97a6-05ee10807bc3"
    password = "192292"

    async with async_session() as db:
        imp = await db.get(Import, import_id)
        if not imp:
            print("Import not found")
            return
        print(f"Status: {imp.status}")

        # Parse the PDF
        invoice = process_pdf(file_path, password=password)
        print(f"Bank: {invoice.bank}")
        print(f"Items: {len(invoice.items)}")
        for item in invoice.items:
            print(f"  {item.description[:40]:40s} | {item.amount:>8} | hint={item.category_hint}")

        # Confirm & persist
        saved, dupes, errors = await confirm_import(
            db, invoice, account_id, import_id=import_id
        )
        print(f"\nSaved: {saved}, Duplicates: {dupes}, Errors: {errors}")

if __name__ == "__main__":
    asyncio.run(main())
