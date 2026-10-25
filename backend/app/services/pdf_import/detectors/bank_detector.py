from app.services.pdf_import.detectors.base import BaseBankDetector, BankIdentification

BANK_SIGNATURES: list[tuple[str, str, list[str]]] = [
    ("nubank", "Nubank", ["nubank", "roxinho", "nu conta", "nuconta"]),
    ("inter", "Banco Inter", ["banco inter", "intermed", "inter pag"]),
    ("itau", "Itaú", ["itau", "itaú", "itaú unibanco"]),
    ("santander", "Santander", ["santander", "banco santander"]),
    ("bb", "Banco do Brasil", ["banco do brasil", "banco brasil", "bb"]),
    ("c6", "C6 Bank", ["c6 bank", "c6bank"]),
    ("caixa", "Caixa Econômica", ["caixa econômica", "caixa federal", "caixa economica"]),
    ("bradesco", "Bradesco", ["bradesco", "banco bradesco"]),
]


class SignatureBankDetector(BaseBankDetector):
    def detect(self, text: str) -> BankIdentification:
        lower = text.lower()
        best_code = "unknown"
        best_name = "Desconhecido"
        best_confidence = 0.0

        for code, name, keywords in BANK_SIGNATURES:
            matches = sum(1 for kw in keywords if kw in lower)
            if matches == 0:
                continue
            confidence = min(matches / len(keywords) + 0.1, 1.0)
            if confidence > best_confidence:
                best_confidence = confidence
                best_code = code
                best_name = name

        return BankIdentification(
            bank_code=best_code,
            bank_name=best_name,
            confidence=best_confidence,
        )
