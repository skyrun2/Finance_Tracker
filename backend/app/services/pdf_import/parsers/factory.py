from app.services.pdf_import.parsers.base import BaseCreditCardParser
from app.services.pdf_import.parsers.inter_pdf_parser import InterPdfParser
from app.services.pdf_import.parsers.nubank_pdf_parser import NubankPdfParser


_registered_pdf_parsers: list[type[BaseCreditCardParser]] = [
    InterPdfParser,
    NubankPdfParser,
]


def register_pdf_parser(parser_cls: type[BaseCreditCardParser]) -> None:
    _registered_pdf_parsers.append(parser_cls)


def get_pdf_parser(bank_code: str) -> BaseCreditCardParser:
    for cls in _registered_pdf_parsers:
        parser = cls()
        if parser.can_parse(bank_code):
            return parser
    raise ValueError(f"Nenhum parser encontrado para o banco: {bank_code}")
