from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ExtractedPDFData:
    text: str
    tables: list[list[list[str | None]]]
    pages: int
    raw_pages: list[dict] = field(default_factory=list)


class BasePdfExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> ExtractedPDFData:
        ...
