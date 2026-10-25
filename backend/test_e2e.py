"""E2E test: create accounts, import files, verify results."""
import httpx
import json
from pathlib import Path

BASE = "http://localhost:8000/api/v1"
c = httpx.Client()

# 1. Create checking account
r = c.post(f"{BASE}/accounts", json={"name": "Conta Corrente", "type": "CHECKING", "balance": 5000})
assert r.is_success, f"Create account failed: {r.text}"
acc_id = r.json()["id"]
print(f"Conta corrente criada: {acc_id[:8]}...")

# 2. Create credit card account
r = c.post(f"{BASE}/accounts", json={"name": "Cartao Nubank", "type": "CREDIT_CARD", "balance": 0})
assert r.is_success, f"Create card failed: {r.text}"
card_id = r.json()["id"]
print(f"Cartao criado: {card_id[:8]}...")

# 3. List categories
r = c.get(f"{BASE}/categories")
cats = r.json()
print(f"Categorias carregadas: {len(cats)}")

# 4. Import bank statement
csv_path = Path(__file__).parent / "test_extrato_inter.csv"
with open(csv_path, "rb") as f:
    r = c.post(
        f"{BASE}/imports/bank-statement",
        data={"account_id": acc_id},
        files={"file": ("extrato.csv", f, "text/csv")},
    )
    assert r.is_success, f"Import bank failed: {r.text}"
res = r.json()
print(f"Import extrato: status={res['status']}, saved={res['summary']['saved']}, "
      f"dups={res['summary']['duplicates']}, errors={res['summary']['errors']}")

# 5. Import again (dedup test via checksum)
with open(csv_path, "rb") as f:
    r = c.post(
        f"{BASE}/imports/bank-statement",
        data={"account_id": acc_id},
        files={"file": ("extrato.csv", f, "text/csv")},
    )
if r.status_code == 409:
    print("Dedup OK: arquivo duplicado rejeitado (409)")
else:
    res2 = r.json()
    print(f"Re-import: saved={res2['summary']['saved']} (esperado 0)")

# 6. Import credit card invoice
csv_path2 = Path(__file__).parent / "test_fatura_nubank.csv"
with open(csv_path2, "rb") as f:
    r = c.post(
        f"{BASE}/imports/credit-card",
        data={"account_id": card_id},
        files={"file": ("fatura.csv", f, "text/csv")},
    )
assert r.is_success, f"Import card failed: {r.text}"
res = r.json()
print(f"Import fatura: status={res['status']}, saved={res['summary']['saved']}, "
      f"dups={res['summary']['duplicates']}, errors={res['summary']['errors']}")

# 7. List imports
r = c.get(f"{BASE}/imports")
data = r.json()["data"]
print(f"\nImportacoes registradas: {r.json()['total']}")
for imp in data:
    print(f"  - {imp['filename'][:30]:30s} {imp['status']:10s} {imp['transaction_count']} transacoes")

# 8. List transactions with category classification
r = c.get(f"{BASE}/transactions?per_page=50")
txns = r.json()["data"]
print(f"\nTransacoes: {r.json()['total']} total")
for t in txns:
    cat = t.get("category_name") or "?"
    print(f"  R$ {float(t['amount']):>8.2f} {t['type']:8s} {t['description'][:45]:45s} [{cat}]")

# 9. Dashboard
r = c.get(f"{BASE}/dashboard/summary")
d = r.json()
print(f"\nDashboard: R$ {float(d['total_balance']):.2f} saldo")
print(f"  Receitas mes:   R$ {float(d['monthly_income']):.2f}")
print(f"  Despesas mes:   R$ {float(d['monthly_expense']):.2f}")
print(f"  Categorias:     {len(d['expenses_by_category'])} com gastos")
for ec in d["expenses_by_category"]:
    print(f"    - {ec['name']:20s} R$ {float(ec['total']):>8.2f}")

print("\nE2E test PASSED!")
