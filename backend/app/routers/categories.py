from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Category, Transaction
from app.schemas import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


def _cycle_range(month: int, year: int) -> tuple[date, date]:
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    start = date(prev_year, prev_month, 6)
    end = date(year, month, 6)
    return start, end


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    month: int | None = Query(None),
    year: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    year = year or today.year
    month = month or today.month
    cycle_start, cycle_end = _cycle_range(month, year)

    result = await db.execute(select(Category).where(Category.is_active == True))
    categories = result.scalars().all()

    spending_result = await db.execute(
        select(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(
            Transaction.type == "EXPENSE",
            Transaction.category_id.isnot(None),
            Transaction.transaction_date >= cycle_start,
            Transaction.transaction_date <= cycle_end,
        )
        .group_by(Transaction.category_id)
    )
    spending_map = {row[0]: Decimal(str(row[1])) for row in spending_result}

    for cat in categories:
        cat.spending = spending_map.get(cat.id, Decimal("0"))

    return categories


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category or not category.is_active:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, data: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category or not category.is_active:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.is_system:
        raise HTTPException(status_code=400, detail="Default categories cannot be modified")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category or not category.is_active:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.is_system:
        raise HTTPException(status_code=400, detail="Default categories cannot be deleted")
    category.is_active = False
    await db.commit()
