import re

from app.services.pdf_import.invoice_data import ParsedLineItem
from app.services.parsers.base import ParsedTransaction


def normalize_item(item: ParsedLineItem) -> ParsedTransaction:
    desc = item.description
    desc = re.sub(r"\s+", " ", desc).strip()

    if item.is_payment or item.is_reversal:
        txn_type = "INCOME"
    else:
        txn_type = "EXPENSE"

    return ParsedTransaction(
        description=desc,
        amount=item.amount,
        transaction_date=item.transaction_date,
        type=txn_type,
        original_description=item.original_description,
        category_hint=item.category_hint,
        installment_number=item.installment_number,
        total_installments=item.total_installments,
        fingerprint=item.fingerprint,
    )


def normalize_items(items: list[ParsedLineItem]) -> list[ParsedTransaction]:
    return [normalize_item(item) for item in items]
