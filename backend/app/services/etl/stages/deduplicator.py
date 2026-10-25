"""Stage 4: Deduplicate transactions using fingerprint hashing."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction


async def find_duplicates(
    db: AsyncSession,
    fingerprints: set[str],
    account_id: int | None = None,
) -> set[str]:
    """Return the subset of fingerprints that already exist in the database."""
    stmt = select(Transaction.fingerprint).where(
        Transaction.fingerprint.in_(fingerprints)
    )
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)

    result = await db.execute(stmt)
    return {row[0] for row in result}


def detect_duplicates_in_batch(
    transactions: list, existing_fingerprints: set[str]
) -> tuple[list, list]:
    """Split transactions into new and duplicate."""
    new = []
    duplicates = []
    for txn in transactions:
        if txn.fingerprint in existing_fingerprints:
            duplicates.append(txn)
        else:
            new.append(txn)
    return new, duplicates
