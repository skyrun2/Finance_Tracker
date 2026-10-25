from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class ParsedTransaction:
    description: str
    amount: Decimal
    transaction_date: date
    type: str
    original_description: str = ""
    category_hint: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    external_id: Optional[str] = None
    fingerprint: str = ""
    original_type: Optional[str] = None


@dataclass
class ParseResult:
    transactions: list[ParsedTransaction] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_rows: int = 0
    processed_rows: int = 0


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        ...

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        ...

    def get_instituition_name(self) -> str:
        return "Unknown"

    def generate_fingerprint(self, txn: ParsedTransaction) -> str:
        import hashlib

        raw = f"{txn.transaction_date}|{txn.amount}|{txn.description}"
        return hashlib.sha256(raw.encode()).hexdigest()
