from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import accounts, categories, dashboard, goals, imports, investments, transactions

 
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db() 
    await _seed_default_categories()
    yield


async def _seed_default_categories():
    from sqlalchemy import select
    from app.database import async_session
    from app.models import Category

    async with async_session() as db:
        result = await db.execute(select(Category).where(Category.is_system == True).limit(1))
        if result.scalar_one_or_none():
            return

        defaults = [
            Category(name="Food & Dining", type="EXPENSE", icon="shopping-cart", color="#ef4444", is_system=True),
            Category(name="Transportation", type="EXPENSE", icon="car", color="#f97316", is_system=True),
            Category(name="Entertainment", type="EXPENSE", icon="gamepad-2", color="#a855f7", is_system=True),
            Category(name="Subscriptions", type="EXPENSE", icon="repeat", color="#64748b", is_system=True),
            Category(name="Shopping", type="EXPENSE", icon="package", color="#f43f5e", is_system=True),
            Category(name="Investments", type="INCOME", icon="trending-up", color="#22c55e", is_system=True),
            Category(name="Other", type="EXPENSE", icon="ellipsis", color="#6b7280", is_system=True),
        ]
        db.add_all(defaults)
        await db.commit()


app = FastAPI(
    title="finance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(imports.router)
app.include_router(investments.router)
app.include_router(dashboard.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
