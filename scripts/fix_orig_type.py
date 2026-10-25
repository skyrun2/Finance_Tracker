"""Fix original_type for existing TRANSFER transactions based on description."""
import sqlite3
import re

conn = sqlite3.connect("backend/finance.db")
c = conn.cursor()

# Find all TRANSFER transactions with NULL original_type
c.execute("SELECT id, description, amount, type FROM transactions WHERE type = 'TRANSFER' AND original_type IS NULL")
txns = c.fetchall()
print(f"Found {len(txns)} TRANSFER transactions without original_type")

for tid, desc, amt, typ in txns:
    lower = desc.lower()
    if "resgate" in lower:
        orig = "INCOME"
    elif "aplica" in lower or "pagamento fatura" in lower or "fatura" in lower:
        orig = "EXPENSE"
    elif "pix" in lower and "lucas rocha" in lower:
        # Check if it's a Pix enviado (outgoing) or recebido (incoming)
        if "recebido" in lower:
            orig = "INCOME"
        else:
            orig = "EXPENSE"
    else:
        # Default: use the direction implied by the amount
        orig = "EXPENSE"

    c.execute("UPDATE transactions SET original_type = ? WHERE id = ?", (orig, tid))
    print(f"  {tid[:8]} | {desc[:40]:40s} | R$ {float(amt):>6.2f} | {orig}")

conn.commit()

# Now recalculate account balances
for aid, aname in [("e4ebbc4b-02f0-4bc3-a0df-c57a637ac09e", "Lro"),
                    ("bea45e7b-bba2-4cfe-97a6-05ee10807bc3", "Lro credito")]:
    c.execute("SELECT amount, type, original_type FROM transactions WHERE account_id = ?", (aid,))
    txns2 = c.fetchall()
    balance = 0.0
    for amt, typ, orig in txns2:
        effective = orig if orig else typ
        if effective == "INCOME":
            balance += float(amt)
        else:
            balance -= float(amt)
    c.execute("UPDATE accounts SET balance = ? WHERE id = ?", (balance, aid))
    print(f"\n{aname}: R$ {balance:.2f}")

conn.commit()
conn.close()
print("\nDone")
