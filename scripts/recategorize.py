"""Recategorize all existing transactions using the updated rules."""
import asyncio
import sys
sys.path.insert(0, 'backend')

from app.database import async_session
from app.models import Category, Transaction
from app.services.etl.stages.classifier import DEFAULT_RULES, _matches_rule
from sqlalchemy import select


async def main():
    async with async_session() as db:
        # Load all categories
        result = await db.execute(select(Category))
        categories = {c.name: c for c in result.scalars().all()}
        active_cat_ids = {c.id for c in categories.values() if c.is_active}
        print(f"Active categories: {[c.name for c in categories.values() if c.is_active]}")
        print(f"Inactive categories: {[c.name for c in categories.values() if not c.is_active]}")

        # Load all transactions
        result = await db.execute(select(Transaction))
        txns = result.scalars().all()
        print(f"Total transactions: {len(txns)}")

        updated = 0
        cleared = 0
        for txn in txns:
            # Clear category if it's now inactive
            if txn.category_id and txn.category_id not in active_cat_ids:
                txn.category_id = None
                cleared += 1
                continue

            desc_lower = (txn.description or "").lower()
            new_cat_id = None

            for pattern, rule_type, category_name in DEFAULT_RULES:
                if _matches_rule(desc_lower, pattern, rule_type):
                    cat = categories.get(category_name)
                    if cat:
                        new_cat_id = cat.id
                        break

            # Fallback: qualquer coisa sem match vai pra Outros
            if not new_cat_id:
                outros = categories.get("Outros")
                if outros:
                    new_cat_id = outros.id

            if new_cat_id and txn.category_id != new_cat_id:
                txn.category_id = new_cat_id
                updated += 1

        await db.commit()
        print(f"Cleared {cleared} transactions with inactive categories")
        print(f"Updated {updated} transactions")


if __name__ == "__main__":
    asyncio.run(main())
