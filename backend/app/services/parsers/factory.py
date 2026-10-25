"""Parser factory - selects the right parser for the file."""

from app.services.parsers.base import BaseParser
from app.services.parsers.generic_parser import GenericParser


_registered_parsers: list[type[BaseParser]] = [
    GenericParser,  # Must be last (fallback) for now the only BankParser and made almost solely for Opay
]


def register_parser(parser_cls: type[BaseParser]) -> None:
    _registered_parsers.insert(len(_registered_parsers) - 1, parser_cls)


def get_parser(file_path: str) -> BaseParser:
    for cls in _registered_parsers:
        parser = cls()
        if parser.can_parse(file_path):
            return parser
        print(parser)
    return GenericParser()
