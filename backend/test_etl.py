import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select

from app.database import async_session, init_db
from app.models import Account
from app.services.etl.pipeline import ETLPipeline


async def test():
    await init_db()
    async with async_session() as db:
        accounts = await db.execute(select(Account).where(Account.is_active == True))
        account = accounts.scalars().first()
        if not account:
            print("No account found")
            return

        pipeline = ETLPipeline(db)
        result = await pipeline.run(
            "uploads/280f133b-9ea9-4396-89d8-231586a353a9.csv", "csv", account.id
        )
        print(f"Status: {result['status']}")
        print(f"Total: {result['total']}, Processed: {result['processed']}")
        print(f"Errors: {result['errors'][:3]}")
        for t in result["transactions"][:5]:
            print(
                f"  {t['transaction_date']} | {t['description'][:45]:45s} | {t['amount']:>8.2f} | {t['type']}"
            )


asyncio.run(test())
