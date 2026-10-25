"""ETL Pipeline orchestrator.

Usage:
    from app.services.etl.pipeline import run_pipeline
    result = await run_pipeline(db, file_path, account_id, import_id)
"""

import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Import, Account, Transaction
from app.services.etl.stages.validator import validate_file
from app.services.etl.stages.normalizer import normalize_description
from app.services.etl.stages.deduplicator import find_duplicates, detect_duplicates_in_batch
from app.services.etl.stages.persister import persist_transactions_batch
from app.services.parsers.factory import get_parser

logger = logging.getLogger(__name__)


class PipelineResult:
    def __init__(
        self,
        total_parsed: int = 0,
        saved: int = 0,
        duplicates: int = 0,
        errors: list[str] | None = None,
        import_errors: list[dict] | None = None,
    ):
        self.total_parsed = total_parsed
        self.saved = saved
        self.duplicates = duplicates
        self.errors = errors or []
        self.import_errors = import_errors or []


async def run_pipeline(
    db: AsyncSession,
    file_path: str,
    account_id: str,
    import_id: Optional[str] = None,
    update_import_status: bool = True,
) -> PipelineResult:
    result = PipelineResult()

    # 1. Validate file
    validation = validate_file(file_path)
    if not validation.valid:
        result.errors = validation.errors
        if import_id and update_import_status:
            await _update_import_status(db, import_id, "error", "\n".join(validation.errors))
        return result

    print("validated")
    # 2. Parse using bank-specific parser
    parser = get_parser(file_path)
    parse_result = parser.parse(file_path)
    result.total_parsed = parse_result.total_rows
    # print(parse_result)
    if parse_result.errors:
        result.errors = parse_result.errors[:20]  # limit errors

    if not parse_result.transactions:
        if import_id and update_import_status:
            await _update_import_status(db, import_id, "error", "No transactions found")
        return result

    # 3. Normalize descriptions
    for txn in parse_result.transactions:
        txn.description = normalize_description(txn.description)

    # 4. Classify transactions
    from app.services.etl.stages.classifier import classify_transaction

    for txn in parse_result.transactions:
        classification = await classify_transaction(
            db=db,
            description=txn.description,
            amount=txn.amount,
            transaction_type=txn.type,
            category_hint=txn.category_hint,
        )
        # Store classification metadata on transaction objects
        txn._category_id = classification.category_id
        txn._subcategory_id = classification.subcategory_id
        txn._confidence = classification.confidence

    # 4b. Detect internal PIX transfers (between own accounts)
    _detect_internal_transfers(parse_result.transactions)

    # 5. Deduplicate
    fingerprints = {t.fingerprint for t in parse_result.transactions}
    existing = await find_duplicates(db, fingerprints, account_id)
    new_txns, dup_txns = detect_duplicates_in_batch(parse_result.transactions, existing)
    result.duplicates = len(dup_txns)

    if not new_txns:
        if import_id and update_import_status:
            await _update_import_status(db, import_id, "completed", "All the transactions already existed")
        return result

    # 6. Persist
    saved, persist_errors = await persist_transactions_batch(
        db, account_id, new_txns, import_id=import_id
    )
    result.saved = len(saved)
    result.import_errors = persist_errors

    if saved and not persist_errors:
        await db.commit()

    # 7. Finalize
    if import_id and update_import_status:
        summary_lines = [
            f"Processed: {result.total_parsed}",
            f"Imported: {result.saved}",
            f"Duplicates: {result.duplicates}",
        ]
        if result.errors:
            summary_lines.append(f"Parsing errors: {len(result.errors)}")
        if persist_errors:
            summary_lines.append(f"Persistence errors: {len(persist_errors)}")
        status = "completed" if result.saved > 0 else "error"
        await _update_import_status(db, import_id, status, "\n".join(summary_lines))
    print(result)
    return result


async def _update_import_status(
    db: AsyncSession, import_id: str, status: str, summary: str = ""
) -> None:
    try:
        import_record = await db.get(Import, import_id)
        if import_record:
            import_record.status = status
            import_record.summary = summary
            import_record.processed_at = datetime.utcnow()
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating import status {import_id}: {e}")


def _detect_internal_transfers(transactions: list) -> None:
    PATTERNS = [
        ["PIX", "Lucas Rocha"],
        ["bill payment"],
        ["bill", "card"],
        ["investment", "CDB"],
        ["redemption", "CDB"],
    ]
    for txn in transactions:
        desc_lower = txn.description.lower()
        for parts in PATTERNS:
            if all(p in desc_lower for p in parts):
                txn.original_type = txn.type
                txn.type = "TRANSFER"
                break


def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


async def process_import(
    import_id: str,
    file_path: str,
    file_type: str,
    account_id: str,
    db: AsyncSession,
) -> PipelineResult:
    """Legacy wrapper for the ETL pipeline (called by old import endpoint)."""
    result = await run_pipeline(db, file_path, account_id, import_id)
    return result
