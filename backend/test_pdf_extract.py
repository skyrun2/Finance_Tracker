import sys; sys.path.insert(0, '.')
from app.services.pdf_import.pdf_pipeline import process_pdf, build_preview

for label, path in [("INTER", "test_fatura_inter.pdf"), ("NUBANK", "test_fatura_nubank.pdf")]:
    print(f"\n=== {label} ===")
    invoice = process_pdf(path)
    preview = build_preview(invoice)
    print(f"Banco: {preview.bank}")
    print(f"Cartao final: {preview.card_last_four}")
    print(f"Fechamento: {preview.closing_date}")
    print(f"Vencimento: {preview.due_date}")
    print(f"Total fatura: {preview.total_amount}")
    print(f"Soma itens: {preview.items_sum}")
    print(f"Itens: {preview.items_count}")
    print(f"Warnings: {preview.warnings}")
    for item in preview.items:
        print(f"  {item['transaction_date']} | {item['description'][:40]:40s} | R$ {item['amount']:>8s} | parc={item['installment_number']} | fee={item['is_fee']} | rev={item['is_reversal']}")
