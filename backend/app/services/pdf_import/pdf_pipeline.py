import hashlib
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Import
from app.services.pdf_import.detectors.bank_detector import SignatureBankDetector
from app.services.pdf_import.extractors.pdfplumber_extractor import PdfplumberExtractor
from app.services.pdf_import.invoice_data import CreditCardInvoice, InvoicePreview
from app.services.pdf_import.normalizer import normalize_items
from app.services.pdf_import.parsers.factory import get_pdf_parser
from app.services.etl.stages.deduplicator import find_duplicates
from app.services.etl.stages.persister import persist_transactions_batch
from app.services.etl.stages.classifier import classify_transaction

logger = logging.getLogger(__name__)


class PdfPipelineResult:
    def __init__(
        self,
        invoice: CreditCardInvoice,
        total_value: Optional[str] = None,
        saved: int = 0,
        duplicates: int = 0,
        errors: list[str] | None = None,
    ):
        self.invoice = invoice
        self.total_value = total_value
        self.saved = saved
        self.duplicates = duplicates
        self.errors = errors or []


def process_pdf(file_path: str, password: str | None = None) -> CreditCardInvoice:
    extractor = PdfplumberExtractor()
    try:
        extracted = extractor.extract(file_path, password=password)
    except Exception as e:
        msg = str(e) or "Erro desconhecido ao processar o PDF"
        raise RuntimeError(msg)

    if not extracted.text.strip():
        raise RuntimeError("Não foi possível extrair texto do PDF. O arquivo pode ser escaneado (imagem) ou estar corrompido.")

    detector = SignatureBankDetector()
    bank_id = detector.detect(extracted.text)

    if bank_id.bank_code == "unknown":
        invoice = CreditCardInvoice(bank="Desconhecido")
        invoice.warnings.append(
            f"Banco não identificado no PDF. "
            f"Conteúdo extraído: {extracted.text[:300]}..."
        )
        return invoice

    parser = get_pdf_parser(bank_id.bank_code)
    invoice = parser.parse(extracted)
    invoice.bank = bank_id.bank_name

    return invoice


def build_preview(invoice: CreditCardInvoice) -> InvoicePreview:
    total_sum = sum(item.amount for item in invoice.items if not item.is_payment)

    items_data = []
    for item in invoice.items:
        items_data.append({
            "transaction_date": item.transaction_date.isoformat(),
            "description": item.description,
            "amount": str(item.amount),
            "installment_number": item.installment_number,
            "total_installments": item.total_installments,
            "is_fee": item.is_fee,
            "is_payment": item.is_payment,
            "is_reversal": item.is_reversal,
            "category_hint": item.category_hint,
        })

    is_valid = len(invoice.warnings) == 0 and len(invoice.items) > 0

    return InvoicePreview(
        bank=invoice.bank,
        card_last_four=invoice.card_last_four,
        closing_date=invoice.closing_date.isoformat() if invoice.closing_date else None,
        due_date=invoice.due_date.isoformat() if invoice.due_date else None,
        total_amount=str(invoice.total_amount) if invoice.total_amount else None,
        items_count=len(invoice.items),
        items_sum=str(total_sum),
        items=items_data,
        warnings=invoice.warnings,
        is_valid=is_valid,
    )


async def confirm_import(
    db: AsyncSession,
    invoice: CreditCardInvoice,
    account_id: str,
    import_id: Optional[str] = None,
) -> tuple[int, int, list[str]]:
    txns = normalize_items(invoice.items)
    persist_errors: list[dict] = []
    saved_count = 0

    for item in invoice.items:
        txn_data = normalize_items([item])[0]

        classification = await classify_transaction(
            db=db,
            description=txn_data.description,
            amount=txn_data.amount,
            transaction_type=txn_data.type,
            category_hint=txn_data.category_hint or item.category_hint,
        )
        txn_data._category_id = classification.category_id
        txn_data._subcategory_id = classification.subcategory_id
        txn_data._confidence = classification.confidence

    fingerprints = {t.fingerprint for t in txns}
    existing = await find_duplicates(db, fingerprints, account_id)
    new_txns = [t for t in txns if t.fingerprint not in existing]
    dup_count = len(txns) - len(new_txns)

    if not new_txns:
        return 0, dup_count, []

    saved, persist_errors = await persist_transactions_batch(
        db, account_id, new_txns, import_id=import_id
    )
    saved_count = len(saved)
    error_messages = [e["error"] for e in persist_errors]

    if saved_count > 0 and not persist_errors:
        await db.commit()

    if import_id:
        try:
            import_record = await db.get(Import, import_id)
            if import_record:
                import_record.status = "completed" if saved_count > 0 else "error"
                import_record.processed_rows = saved_count
                import_record.summary = (
                    f"Importadas: {saved_count}, "
                    f"Duplicatas: {dup_count}, "
                    f"Erros: {len(persist_errors)}"
                )
                import_record.processed_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar import {import_id}: {e}")

    return saved_count, dup_count, error_messages
