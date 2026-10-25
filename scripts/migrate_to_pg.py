"""Migrate data from SQLite to PostgreSQL.

Usage (local test):
    python scripts/migrate_to_pg.py

Usage (Railway):
    DATABASE_URL=postgresql+asyncpg://... python scripts/migrate_to_pg.py
"""
import asyncio
import os
import sys

sys.path.insert(0, "backend")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./finance.db")

from app.config import settings
from app.models import Base

PG_URL = settings.async_database_url
PG_SYNC_URL = PG_URL.replace("+asyncpg", "").replace("postgresql+", "postgresql+")


def migrate():
    print(f"SQLite: {settings.DATABASE_URL}")
    print(f"PostgreSQL: {PG_URL}")

    sqlite = create_engine("sqlite:///finance.db")
    pg = create_engine(PG_SYNC_URL.replace("+asyncpg", ""))

    # Create PostgreSQL tables
    Base.metadata.create_all(pg)
    print("Created PostgreSQL tables")

    sqlite_conn = sqlite.connect()
    pg_conn = pg.connect()
    pg_trans = pg_conn.begin()

    tables_order = [
        "accounts",
        "categories",
        "subcategories",
        "imports",
        "investments",
        "investment_history",
        "goals",
        "classification_rules",
        "transactions",
    ]

    try:
        for table in tables_order:
            # Read from SQLite
            rows = sqlite_conn.execute(text(f"SELECT * FROM {table}")).fetchall()
            if not rows:
                print(f"  {table}: 0 rows (skip)")
                continue

            columns = list(rows[0]._fields)
            placeholders = ", ".join([f":{c}" for c in columns])
            col_names = ", ".join(columns)

            for row in rows:
                data = dict(zip(columns, row))
                # Handle boolean types from SQLite (0/1 → True/False)
                for k, v in data.items():
                    if isinstance(v, int) and k in (
                        "is_active", "is_system", "is_recurring",
                        "include_in_dashboard",
                    ):
                        data[k] = bool(v)

                try:
                    pg_conn.execute(
                        text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"),
                        data,
                    )
                except Exception as e:
                    print(f"  Error on {table} id={data.get('id', '?')}: {e}")
                    pg_trans.rollback()
                    raise

            print(f"  {table}: {len(rows)} rows migrated")

        pg_trans.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        pg_trans.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    migrate()
