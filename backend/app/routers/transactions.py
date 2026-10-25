from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Category, Account, Transaction
from app.schemas import (
    PaginatedResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=PaginatedResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    account_id: str | None = Query(None),
    category_id: str | None = Query(None),
    type: str | None = Query(None),
    status: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).options(
        joinedload(Transaction.account),
        joinedload(Transaction.category),
    )

    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if type:
        query = query.where(Transaction.type == type)
    if status:
        query = query.where(Transaction.status == status)
    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    if search:
        query = query.where(Transaction.description.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Transaction.transaction_date.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    transactions = result.unique().scalars().all()

    data = []
    for t in transactions:
        resp = TransactionResponse.model_validate(t)
        resp.account_name = t.account.name if t.account else None
        resp.category_name = t.category.name if t.category else None
        data.append(resp)

    return PaginatedResponse(data=[d.model_dump() for d in data], total=total, page=page, per_page=per_page)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, data.account_id)
    if not account or not account.is_active:
        raise HTTPException(status_code=404, detail="Account not found")

    if data.category_id:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    txn = Transaction(**data.model_dump())
    db.add(txn)

    if data.type == "EXPENSE":
        account.balance = float(account.balance or 0) - float(data.amount)
    elif data.type == "INCOME":
        account.balance = float(account.balance or 0) + float(data.amount)

    await db.commit()
    await db.refresh(txn)
    return TransactionResponse.model_validate(txn)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    txn = await db.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    result = TransactionResponse.model_validate(txn)
    if txn.account:
        result.account_name = txn.account.name
    if txn.category:
        result.category_name = txn.category.name
    return result


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, data: TransactionUpdate, db: AsyncSession = Depends(get_db)):
    txn = await db.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    old_amount = float(txn.amount) if txn.amount else 0
    old_type = txn.type

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, key, value)

    if data.amount is not None or data.type is not None:
        account = await db.get(Account, txn.account_id)
        if account:
            if old_type == "EXPENSE":
                account.balance = float(account.balance or 0) + old_amount
            elif old_type == "INCOME":
                account.balance = float(account.balance or 0) - old_amount

            new_amount = float(data.amount) if data.amount else old_amount
            new_type = data.type if data.type else old_type
            if new_type == "EXPENSE":
                account.balance = float(account.balance or 0) - new_amount
            elif new_type == "INCOME":
                account.balance = float(account.balance or 0) + new_amount

    await db.commit()
    await db.refresh(txn)
    return TransactionResponse.model_validate(txn)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    txn = await db.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    account = await db.get(Account, txn.account_id)
    if account:
        if txn.type == "EXPENSE":
            account.balance = float(account.balance or 0) + float(txn.amount)
        elif txn.type == "INCOME":
            account.balance = float(account.balance or 0) - float(txn.amount)

    await db.delete(txn)
    await db.commit()
