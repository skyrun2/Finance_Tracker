from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str
    type: str = Field(pattern=r"^(CHECKING|SAVINGS|CREDIT_CARD|INVESTMENT)$")
    balance: Decimal = Decimal("0")
    currency: str = "NGN"
    color: Optional[str] = None
    include_in_dashboard: bool = True


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    balance: Optional[Decimal] = None
    currency: Optional[str] = None
    color: Optional[str] = None
    include_in_dashboard: Optional[bool] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: str
    name: str
    type: str
    balance: Decimal
    currency: str
    color: Optional[str]
    include_in_dashboard: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    type: str = Field(pattern=r"^(INCOME|EXPENSE)$")
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    type: str
    icon: Optional[str]
    color: Optional[str]
    is_system: bool
    is_active: bool
    created_at: datetime
    spending: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    account_id: str
    category_id: Optional[str] = None
    description: str
    amount: Decimal
    type: str = Field(pattern=r"^(INCOME|EXPENSE|TRANSFER)$")
    status: str = "CLEARED"
    transaction_date: date
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    is_recurring: bool = False
    external_id: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    account_id: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[str] = None
    status: Optional[str] = None
    transaction_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    category_id: Optional[str]
    subcategory_id: Optional[str] = None
    description: str
    original_description: Optional[str]
    amount: Decimal
    type: str
    status: str
    transaction_date: date
    due_date: Optional[date]
    payment_date: Optional[date]
    is_recurring: bool
    fingerprint: Optional[str] = None
    import_id: Optional[str] = None
    notes: Optional[str]
    created_at: datetime
    account_name: Optional[str] = None
    category_name: Optional[str] = None

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    category_id: Optional[str] = None
    name: str
    target_amount: Decimal
    current_amount: Decimal = Decimal("0")
    month: Optional[str] = None
    year: int
    type: str = "MONTHLY"
    deadline: Optional[date] = None


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[Decimal] = None
    current_amount: Optional[Decimal] = None
    month: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None
    deadline: Optional[date] = None
    is_active: Optional[bool] = None


class GoalResponse(BaseModel):
    id: str
    category_id: Optional[str]
    name: str
    target_amount: Decimal
    current_amount: Decimal
    month: Optional[str]
    year: int
    type: str
    deadline: Optional[date]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassificationRuleCreate(BaseModel):
    category_id: str
    rule_type: str = Field(pattern=r"^(CONTAINS|REGEX|EQUALS|STARTS_WITH|ENDS_WITH)$")
    pattern: str
    priority: int = 0


class ClassificationRuleResponse(BaseModel):
    id: str
    category_id: str
    rule_type: str
    pattern: str
    priority: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    total_balance: Decimal
    monthly_income: Decimal
    monthly_expense: Decimal
    balance_diff: Decimal
    investment_balance: Decimal = Decimal("0")
    recent_transactions: list[TransactionResponse]
    expenses_by_category: list[dict]


class InvestmentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    current_value: float
    invested_value: float
    type: str
    is_active: bool

    model_config = {"from_attributes": True}


class InvestmentSnapshotRequest(BaseModel):
    value: float


class InvestmentHistoryResponse(BaseModel):
    id: str
    investment_id: str
    value: float
    date: date

    model_config = {"from_attributes": True}


class InvestmentFlowPoint(BaseModel):
    month: int
    year: int
    applied: float
    redeemed: float


class MonthlyHistoryPoint(BaseModel):
    month: int
    year: int
    income: float
    expense: float
    balance: float


class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    per_page: int


class ImportResponse(BaseModel):
    id: str
    account_id: str
    filename: str
    file_type: str
    status: str
    total_rows: int
    processed_rows: int
    error_rows: int
    summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    transaction_count: int = 0

    model_config = {"from_attributes": True}


class ImportDetailResponse(ImportResponse):
    error_log: Optional[dict] = None
    original_filename: Optional[str] = None
