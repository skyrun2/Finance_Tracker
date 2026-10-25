import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, DECIMAL, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    balance: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    include_in_dashboard: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="account", lazy="selectin")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions = relationship("Transaction", back_populates="category", lazy="selectin")
    subcategories = relationship("Subcategory", back_populates="category", lazy="selectin")


class Subcategory(Base):
    __tablename__ = "subcategories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="subcategories", lazy="selectin")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("categories.id"), nullable=True)
    subcategory_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("subcategories.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    original_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="CLEARED")
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    import_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("imports.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    account = relationship("Account", back_populates="transactions", lazy="selectin")
    category = relationship("Category", back_populates="transactions", lazy="selectin")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    current_amount: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(10), default="MONTHLY")
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="UPLOADED")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    current_value: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    invested_value: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # CDI, CDI_PLUS, CRYPTO
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class InvestmentHistory(Base):
    __tablename__ = "investment_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investment_id: Mapped[str] = mapped_column(String(36), ForeignKey("investments.id"), nullable=False)
    value: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    investment = relationship("Investment", lazy="selectin")


class ClassificationRule(Base):
    __tablename__ = "classification_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("categories.id"), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
