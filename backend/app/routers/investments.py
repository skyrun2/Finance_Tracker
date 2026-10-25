from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Investment, InvestmentHistory, Transaction
from app.schemas import (
    InvestmentFlowPoint,
    InvestmentHistoryResponse,
    InvestmentResponse,
    InvestmentSnapshotRequest,
)

router = APIRouter(prefix="/api/v1/investments", tags=["investments"])


@router.get("", response_model=list[InvestmentResponse])
async def list_investments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Investment).where(Investment.is_active == True))
    return result.scalars().all()


@router.post("/{investment_id}/snapshot", response_model=InvestmentResponse)
async def create_snapshot(
    investment_id: str,
    body: InvestmentSnapshotRequest,
    db: AsyncSession = Depends(get_db),
):
    inv = await db.get(Investment, investment_id)
    if not inv:
        raise HTTPException(404, "Investment not found")

    inv.current_value = body.value
    inv.updated_at = date.today()

    snapshot = InvestmentHistory(
        investment_id=investment_id,
        value=body.value,
        date=date.today(),
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(inv)
    return inv


@router.get("/history", response_model=list[InvestmentHistoryResponse])
async def get_history(
    months: int = Query(12),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    from sqlalchemy import func

    cutoff = date.today() - timedelta(days=months * 30)
    result = await db.execute(
        select(InvestmentHistory)
        .where(InvestmentHistory.date >= cutoff)
        .order_by(InvestmentHistory.date)
    )
    return result.scalars().all()


@router.get("/flows", response_model=list[InvestmentFlowPoint])
async def get_flows(
    months: int = Query(2, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    from sqlalchemy import func

    today = date.today()
    first = date(today.year, today.month, 1)
    for _ in range(months - 1):
        if first.month == 1:
            first = date(first.year - 1, 12, 1)
        else:
            first = date(first.year, first.month - 1, 1)

    rows = (
        await db.execute(
            select(
                func.strftime("%m", Transaction.transaction_date).label("month"),
                func.strftime("%Y", Transaction.transaction_date).label("year"),
                Transaction.description,
                func.sum(Transaction.amount).label("total"),
            )
            .where(
                Transaction.transaction_date >= first,
                Transaction.type == "TRANSFER",
            )
            .group_by(
                func.strftime("%m", Transaction.transaction_date),
                func.strftime("%Y", Transaction.transaction_date),
                Transaction.description,
            )
            .order_by(
                func.strftime("%Y", Transaction.transaction_date),
                func.strftime("%m", Transaction.transaction_date),
            )
        )
    ).all()

    result = []
    for month, year, description, total in rows:
        key = f"{year}-{month}"
        point = next((p for p in result if f"{p.year}-{p.month:02d}" == key), None)
        if point is None:
            point = InvestmentFlowPoint(
                month=int(month), year=int(year), applied=0.0, redeemed=0.0
            )
            result.append(point)
        if str(description).lower().startswith("resgat"):
            point.redeemed += float(total)
        elif str(description).lower().startswith("aplica"):
            point.applied += float(total)

    return result
