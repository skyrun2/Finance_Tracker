from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class ParsedLineItem:
    transaction_date: date
    description: str
    amount: Decimal
    original_description: str = ""
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    category_hint: Optional[str] = None
    is_fee: bool = False
    is_payment: bool = False
    is_reversal: bool = False
    fingerprint: str = ""


@dataclass
class CreditCardInvoice:
    bank: str
    card_last_four: Optional[str] = None
    card_holder: Optional[str] = None
    closing_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    currency: str = "NGN"
    items: list[ParsedLineItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_pages: int = 0


@dataclass
class InvoicePreview:
    bank: str
    card_last_four: Optional[str]
    closing_date: Optional[str]
    due_date: Optional[str]
    total_amount: Optional[str]
    items_count: int
    items_sum: str
    items: list[dict]
    warnings: list[str]
    is_valid: bool
