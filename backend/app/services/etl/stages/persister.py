"""Stage 5: Save transactions to the database."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, Transaction
from app.services.etl.stages.classifier import classify_transaction, ClassificationResult


async def persist_transaction(
    db: AsyncSession,
    account_id: str,
    description: str,
    original_description: str,
    amount: Decimal,
    transaction_date: date,
    transaction_type: str,
    fingerprint: str,
    classification: ClassificationResult,
    import_id: Optional[str] = None,
    notes: str = "",
    original_type: Optional[str] = None,
) -> Transaction:
    txn = Transaction(
        account_id=account_id,
        description=description,
        original_description=original_description,
        amount=amount,
        transaction_date=transaction_date,
        type=transaction_type,
        category_id=classification.category_id,
        subcategory_id=classification.subcategory_id,
        fingerprint=fingerprint,
        import_id=import_id,
        notes=notes,
    )
    db.add(txn)
    await db.flush()

    # Update account balance
    stmt = await db.get(Account, account_id)
    if stmt:
        if transaction_type == "TRANSFER":
            effective_type = original_type if original_type else transaction_type
        else:
            effective_type = transaction_type
        if effective_type == "INCOME":
            stmt.balance += amount
        else:
            stmt.balance -= amount

    return txn


async def persist_transactions_batch(
    db: AsyncSession,
    account_id: str,
    transactions: list,
    import_id: Optional[str] = None,
) -> tuple[list[Transaction], list[dict]]:
    saved = []
    errors = []

    for txn_data in transactions:
        try:
            classification = await classify_transaction(
                db=db,
                description=txn_data.description,
                amount=txn_data.amount,
                transaction_type=txn_data.type,
                category_hint=txn_data.category_hint,
            )

            transaction = await persist_transaction(
                db=db,
                account_id=account_id,
                description=txn_data.description,
                original_description=txn_data.original_description,
                amount=txn_data.amount,
                transaction_date=txn_data.transaction_date,
                transaction_type=txn_data.type,
                fingerprint=txn_data.fingerprint,
                classification=classification,
                import_id=import_id,
                original_type=getattr(txn_data, "original_type", None),
            )
            saved.append(transaction)
        except Exception as e:
            errors.append({"description": txn_data.description, "error": str(e)})

    return saved, errors
