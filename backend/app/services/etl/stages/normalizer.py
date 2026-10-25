"""Stage 2: Normalize transaction descriptions."""

import re


COMMON_PATTERNS = [
    (r"pagamento (de )?(boleto|título|titulo) (referente a )?", "Boleto - "),
    (r"transferência (enviada|realizada) (via pix )?(para|a) ", "Pix Enviado - "),
    (r"transferência (recebida|recebimento) (via pix )?(de )?", "Pix Recebido - "),
    (r"comprovante pix (de|para) ", "Pix - "),
    (r"ted (enviada|realizada) ", "TED - "),
    (r"doc (enviado|realizado) ", "DOC - "),
    (r"agendamento (de )?pagamento ", "Agendado - "),
    (r"pagamento (de )?cartão ", "Cartão - "),
    (r"débito automático ", "Débito Automático - "),
    (r"tarifa ", "Tarifa - "),
    (r"iof ", "IOF - "),
    (r"estorno ", "Estorno - "),
    (r"aplicacao ", "Aplicação - "),
    (r"resgate ", "Resgate - "),
    (r"rendimento ", "Rendimento - "),
]

TRIMMABLE_SUFFIXES = [
    r"\s+\(\d+/\d+\)$",            # (1/3)
    r"\s+-\s+\d{2}/\d{2}/\d{4}$",  # - 01/01/2024
    r"\s+-\s+\d{2}/\d{2}/\d{2}$",  # - 01/01/24
]


def normalize_description(desc: str) -> str:
    if not desc:
        return desc

    desc = desc.strip()
    original = desc

    # Apply common patterns
    for pattern, replacement in COMMON_PATTERNS:
        desc = re.sub(pattern, replacement, desc, flags=re.IGNORECASE)

    # Remove trailing date / installment patterns
    for pattern in TRIMMABLE_SUFFIXES:
        desc = re.sub(pattern, "", desc)

    # Collapse whitespace
    desc = re.sub(r"\s+", " ", desc).strip()

    return desc or original
