from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BankIdentification:
    bank_code: str
    bank_name: str
    confidence: float


class BaseBankDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> BankIdentification:
        ...
