from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Account, Category, Transaction
from app.schemas import DashboardSummary, MonthlyHistoryPoint, TransactionResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _cycle_range(month: int, year: int) -> tuple[date, date]:
    """Return (start, end) for the billing cycle.
    Cycle goes from day 6 of previous month to day 6 of current month.
    """
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    start = date(prev_year, prev_month, 6)
    end = date(year, month, 6)
    return start, end


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    month: int | None = Query(None),
    year: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    year = year or today.year
    month = month or today.month
    cycle_start, cycle_end = _cycle_range(month, year)

    total_balance = Decimal("0")

    active_tx_accounts = select(Account.id).where(
        Account.is_active == True
    ).scalar_subquery()

    income_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.type == "INCOME",
            Transaction.account_id.in_(active_tx_accounts),
            Transaction.transaction_date >= cycle_start,
            Transaction.transaction_date <= cycle_end,
        )
    )
    monthly_income = Decimal(str(income_result.scalar()))

    expense_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.type == "EXPENSE",
            Transaction.account_id.in_(active_tx_accounts),
            Transaction.transaction_date >= cycle_start,
            Transaction.transaction_date <= cycle_end,
        )
    )
    monthly_expense = Decimal(str(expense_result.scalar()))
    balance_diff = monthly_income - monthly_expense
    total_balance = balance_diff

    investment_result = await db.execute(
        select(func.coalesce(func.sum(Account.balance), 0))
        .where(Account.type == "INVESTMENT", Account.is_active == True)
    )
    investment_balance = Decimal(str(investment_result.scalar()))

    recent_result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.account), joinedload(Transaction.category))
        .where(Transaction.account_id.in_(active_tx_accounts))
        .order_by(Transaction.transaction_date.desc())
        .limit(10)
    )
    recent_txns = recent_result.unique().scalars().all()

    recent = []
    for t in recent_txns:
        resp = TransactionResponse.model_validate(t)
        resp.account_name = t.account.name if t.account else None
        resp.category_name = t.category.name if t.category else None
        recent.append(resp)

    expenses_by_cat = await db.execute(
        select(
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id, isouter=True)
        .where(
            Transaction.type == "EXPENSE",
            Transaction.account_id.in_(active_tx_accounts),
            Transaction.transaction_date >= cycle_start,
            Transaction.transaction_date <= cycle_end,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    expenses_data = [{"name": row[0], "total": str(row[1])} for row in expenses_by_cat]

    return DashboardSummary(
        total_balance=total_balance,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        balance_diff=balance_diff,
        investment_balance=investment_balance,
        recent_transactions=recent,
        expenses_by_category=expenses_data,
    )


@router.get("/monthly-history", response_model=list[MonthlyHistoryPoint])
async def get_monthly_history(
    months: int = Query(6),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    active_tx_accounts = select(Account.id).where(
        Account.is_active == True
    ).scalar_subquery()

    result = []
    for i in range(months - 1, -1, -1):
        offset = i
        m = today.month - offset
        y = today.year
        while m < 1:
            m += 12
            y -= 1

        start, end = _cycle_range(m, y)

        income_val = await db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.type == "INCOME",
                Transaction.account_id.in_(active_tx_accounts),
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
        )

        expense_val = await db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.type == "EXPENSE",
                Transaction.account_id.in_(active_tx_accounts),
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
        )

        inc = float(income_val or 0)
        exp = float(expense_val or 0)
        result.append(
            MonthlyHistoryPoint(
                month=m,
                year=y,
                income=inc,
                expense=exp,
                balance=inc - exp,
            )
        )
    return result
