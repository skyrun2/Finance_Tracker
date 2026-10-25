import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from dateutil import parser as date_parser

from app.services.pdf_import.extractors.base import ExtractedPDFData
from app.services.pdf_import.invoice_data import CreditCardInvoice, ParsedLineItem
from app.services.pdf_import.parsers.base import BaseCreditCardParser


class NubankPdfParser(BaseCreditCardParser):
    def bank_code(self) -> str:
        return "nubank"

    def can_parse(self, bank_code: str) -> bool:
        return bank_code == "nubank"

    def parse(self, data: ExtractedPDFData) -> CreditCardInvoice:
        invoice = CreditCardInvoice(bank="Nubank")
        text = data.text
        invoice.raw_pages = data.pages

        self._extract_header(invoice, text)
        self._extract_transactions(invoice, data)
        self._validate_total(invoice)

        return invoice

    def _extract_header(self, invoice: CreditCardInvoice, text: str) -> None:
        lines = text.split("\n")

        for line in lines:
            lower = line.strip().lower()

            if "cartão" in lower and "final" in lower:
                m = re.search(r"final\s*[:\s]*(\d{4})", lower)
                if m:
                    invoice.card_last_four = m.group(1)

            if "vencimento" in lower:
                m = re.search(r"(\d{2}/\d{2}/\d{4})", line)
                if m:
                    try:
                        invoice.due_date = date_parser.parse(
                            m.group(1), dayfirst=True
                        ).date()
                    except (ValueError, TypeError):
                        pass

            if "valor total" in lower or "total da fatura" in lower:
                m = re.search(r"([\d.]+,\d{2})", line)
                if m:
                    invoice.total_amount = self._parse_br_amount(m.group(1))

    def _extract_transactions(
        self, invoice: CreditCardInvoice, data: ExtractedPDFData
    ) -> None:
        seen_descriptions: set[str] = set()

        for table in data.tables:
            rows = self._clean_table(table)
            if not rows:
                continue

            header_idx = self._find_data_header(rows)
            if header_idx < 0:
                continue

            data_rows = rows[header_idx + 1:]

            for row in data_rows:
                item = self._parse_row(row)
                if item is None:
                    continue

                dedup_key = (
                    f"{item.transaction_date}|"
                    f"{item.description}|"
                    f"{item.amount}|"
                    f"{item.installment_number or ''}|"
                    f"{item.total_installments or ''}"
                )
                if dedup_key in seen_descriptions:
                    continue
                seen_descriptions.add(dedup_key)

                item.fingerprint = self._generate_fingerprint(item)
                invoice.items.append(item)

    def _clean_table(self, table: list[list[str | None]]) -> list[list[str]]:
        cleaned = []
        for row in table:
            cleaned_row = [(cell or "").strip().replace("\n", " ") for cell in row]
            if any(c for c in cleaned_row if c):
                cleaned.append(cleaned_row)
        return cleaned

    def _find_data_header(self, rows: list[list[str]]) -> int:
        keywords = ["data", "descrição", "descricao", "valor"]
        for i, row in enumerate(rows):
            row_text = " ".join(row).lower()
            matches = sum(1 for kw in keywords if kw in row_text)
            if matches >= 2:
                return i
        return -1

    def _parse_row(self, row: list[str]) -> Optional[ParsedLineItem]:
        if len(row) < 2:
            return None

        date_str, desc = "", ""
        amount_raw = ""

        if len(row) >= 3:
            date_str = row[0].strip()
            desc = row[1].strip()
            amount_raw = row[2].strip()
        elif len(row) == 2:
            desc = row[0].strip()
            amount_raw = row[1].strip()

        if not desc or not amount_raw:
            return None

        if not date_str:
            date_str = self._find_date_in_text(desc)

        if not date_str:
            return None

        try:
            parsed_date = date_parser.parse(date_str, dayfirst=True).date()
        except (ValueError, TypeError):
            return None

        try:
            amount = self._parse_br_amount(amount_raw)
        except (InvalidOperation, ValueError):
            return None

        if amount == 0:
            return None

        installment_num, total_install = self._extract_installments(desc)
        desc_clean = re.sub(r"\s+\(\d+/\d+\)$", "", desc).strip()

        lower_desc = desc.lower()
        is_fee = any(kw in lower_desc for kw in ["iof", "juros", "encargo", "multa", "taxa"])
        is_payment = any(kw in lower_desc for kw in ["pagamento recebido", "pagamento efetuado", "pagto"])
        is_reversal = any(kw in lower_desc for kw in ["estorno", "cancelamento", "reversão", "reversao"])

        category_hint = self._infer_category_hint(desc)
        if is_fee:
            category_hint = None

        return ParsedLineItem(
            transaction_date=parsed_date,
            description=desc_clean,
            amount=abs(amount),
            original_description=desc,
            installment_number=installment_num,
            total_installments=total_install,
            category_hint=category_hint,
            is_fee=is_fee,
            is_payment=is_payment,
            is_reversal=is_reversal,
        )

    def _extract_installments(self, desc: str) -> tuple[Optional[int], Optional[int]]:
        m = re.search(r"(\d+)\s*/\s*(\d+)", desc)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None, None

    def _find_date_in_text(self, text: str) -> Optional[str]:
        m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        return m.group(1) if m else None

    def _validate_total(self, invoice: CreditCardInvoice) -> None:
        if not invoice.items:
            return
        computed = sum(item.amount for item in invoice.items if not item.is_payment)
        if invoice.total_amount is not None:
            diff = abs(computed - invoice.total_amount)
            if diff > Decimal("0.50"):
                invoice.warnings.append(
                    f"Soma dos lançamentos (R$ {computed:.2f}) difere do "
                    f"total da fatura (R$ {invoice.total_amount:.2f}, "
                    f"diferença: R$ {diff:.2f})"
                )

    def _infer_category_hint(self, description: str) -> str | None:
        lower = description.lower()
        if any(kw in lower for kw in ["uber", "99 ", "99t", "taxi", "táxi", "riocard", "mais mobi", "maismobi"]):
            return "Transporte"
        if any(kw in lower for kw in ["ifood", "restaurante", "pizza", "subway", "dogão", "dogao", "hamburguer", "hamburger", "lanchonete", "padaria", "açougue", "acougue"]):
            return "Alimentação"
        if any(kw in lower for kw in ["netflix", "spotify", "spotif", "disney", "hbo", "prime video", "amazon prime", "youtube premium", "apple tv", "apple music", "wellhub"]):
            return "Assinaturas"
        if any(kw in lower for kw in ["amazon", "shopee", "mercado livre", "magalu", "magazine luiza", "shein"]):
            return "Compras"
        if any(kw in lower for kw in ["cinema", "show", "teatro", "ingresso", "passagem aérea", "passagem aerea", "hotel", "viagem", "ticketmaster", "ciclube", "cine"]):
            return "Lazer"
        return None

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
            raise InvalidOperation("Valor vazio")
        return Decimal(raw)

    def _generate_fingerprint(self, item: ParsedLineItem) -> str:
        raw = f"{item.transaction_date}|{item.amount}|{item.description}"
        return hashlib.sha256(raw.encode()).hexdigest()
