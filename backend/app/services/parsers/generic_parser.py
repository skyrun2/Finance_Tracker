import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
from dateutil import parser as date_parser

from app.services.parsers.base import BaseParser, ParseResult, ParsedTransaction

COLUMN_MAP = {
    "description": "description",
    "description": "description",
    "desc": "description",
    "history": "description",
    "history": "description",
    "entry": "description",
    "entry": "description",
    "name": "description",
    "observation": "description",
    "observation": "description",
    "amount": "amount",
    "amount (R$)": "amount",
    "amount": "amount",
    "total": "amount",
    "quantity": "amount",
    "balance": "amount",
    "amount paid": "amount",
    "date": "date",
    "entry date": "date",
    "entry date": "date",
    "entry date": "date",
    "entry date": "date",
    "transaction date": "date",
    "transaction date": "date",
    "due date": "date",
    "due date": "date",
    "accounting period": "date",
    "accounting period": "date",
    "type": "type",
    "debit/credit": "type",
    "debit/credit": "type",
}


class GenericParser(BaseParser):
    def get_instituition_name(self) -> str:
        return "Generic"

    def can_parse(self, file_path: str) -> bool:
        return True

    def parse(self, file_path: str) -> ParseResult:
        ext = file_path.lower().rsplit(".", 1)[-1]
        if ext == "csv":
            return self._parse_csv(file_path)
        elif ext in ("xlsx", "xls"):
            return self._parse_xlsx(file_path)
        return ParseResult(errors=[f"Format .{ext} not supported"])

    def _parse_csv(self, file_path: str) -> ParseResult:
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            content = f.read()

        lines = content.splitlines()
        if not lines:
            return ParseResult(errors=["Empty file"])

        delimiter = self._detect_delimiter(lines)
        header_idx = self._find_header_line(lines, delimiter)
        if header_idx < 0:
            return ParseResult(errors=["Header not found"])

        reader = csv.DictReader(
            io.StringIO("\n".join(lines[header_idx:])), delimiter=delimiter
        )
        rows = [
            {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
            for row in reader
            if any(v.strip() for v in row.values())
        ]
        return self._convert(rows)

    def _parse_xlsx(self, file_path: str) -> ParseResult:
        df = pd.read_excel(file_path, engine="openpyxl")
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.where(pd.notna(df), "")
        rows = df.to_dict(orient="records")
        return self._convert(rows)

    def _detect_delimiter(self, lines: list[str]) -> str:
        sc = sum(1 for line in lines[:6] if ";" in line)
        cc = sum(1 for line in lines[:6] if "," in line)
        return ";" if sc >= cc else ","

    def _find_header_line(self, lines: list[str], delimiter: str) -> int:
        keywords = [
            "date", "description", "description", "desc", "history",
            "history", "entry", "amount", "balance",
        ]
        for i, line in enumerate(lines):
            lower = line.lower()
            if delimiter not in lower:
                continue
            parts = [p.strip().lower() for p in lower.split(delimiter)]
            match_count = sum(1 for p in parts if any(kw in p for kw in keywords))
            if match_count >= 2:
                return i
        return -1

    def _map_columns(self, row: dict) -> dict:
        mapped = {}
        for k, v in row.items():
            target = COLUMN_MAP.get(k, k)
            if target == "description":
                if target in mapped:
                    mapped[target] += " - " + v
                else:
                    mapped[target] = v
            elif target not in mapped:
                mapped[target] = v
        return mapped

    def _parse_br_amount(self, raw: str) -> Decimal:
        raw = raw.strip().replace("R$", "").replace("r$", "").replace(" ", "")
        if "," in raw and "." in raw:
            if raw.rfind(",") > raw.rfind("."):
                raw = raw.replace(".", "").replace(",", ".")
            else:
                raw = raw.replace(",", "")
        elif "," in raw:
            raw = raw.replace(",", ".")
        if not raw:
            raise InvalidOperation("Empty value")
        return Decimal(raw)

    def _convert(self, rows: list[dict]) -> ParseResult:
        result = ParseResult()
        seen = set()

        for row in rows:
            mapped = self._map_columns(row)
            desc = str(mapped.get("description", "")).strip()
            if not desc:
                continue

            # raw_amount = str(mapped.get("amount") or mapped.get("Debit/Credit(₦)") or "0").strip()
            raw_amount = str( mapped.get("debit/credit(₦)","0")).strip()
            try:
                amount = self._parse_br_amount(raw_amount)
            except InvalidOperation:
                result.errors.append(f"Empty value: '{raw_amount}'")
                continue

            raw_date = str(mapped.get("trans. date", "")).strip()
            print(raw_date)
            try:
                parsed_date = date_parser.parse(raw_date, dayfirst=True).date()
            except (ValueError, TypeError):
                result.errors.append(f"Invalid date: '{raw_date}'")
                continue

            fingerprint = f"{desc}|{amount}|{parsed_date}"
            if fingerprint in seen:
                continue
            seen.add(fingerprint)

            txn = ParsedTransaction(
                description=desc,
                amount=abs(amount),
                type="EXPENSE" if amount < 0 else "INCOME",
                transaction_date=parsed_date,
                original_description=desc,
            )
            txn.fingerprint = self.generate_fingerprint(txn)
            result.transactions.append(txn)
            result.processed_rows += 1

        result.total_rows = len(rows)
        return result
