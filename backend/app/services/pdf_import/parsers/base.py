from abc import ABC, abstractmethod

from app.services.pdf_import.extractors.base import ExtractedPDFData
from app.services.pdf_import.invoice_data import CreditCardInvoice


class BaseCreditCardParser(ABC):
    @abstractmethod
    def can_parse(self, bank_code: str) -> bool:
        ...

    @abstractmethod
    def parse(self, data: ExtractedPDFData) -> CreditCardInvoice:
        ...

    def bank_code(self) -> str:
        return "unknown"
