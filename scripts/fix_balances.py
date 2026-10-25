"""Reactivate Investimentos category and recalculate account balances."""
import sqlite3

conn = sqlite3.connect("backend/finance.db")
c = conn.cursor()

# Add original_type column if missing
c.execute("PRAGMA table_info(transactions)")
cols = {r[1] for r in c.fetchall()}
if "original_type" not in cols:
    c.execute("ALTER TABLE transactions ADD COLUMN original_type VARCHAR(20)")
    print("Added original_type column")

# Reactivate Investimentos category
c.execute("UPDATE categories SET is_active = 1 WHERE name = 'Investimentos'")
print("Reactivated Investimentos")

# Fix balance for Lro (checking account)
c.execute(
    "SELECT id, amount, type, original_type FROM transactions "
    "WHERE account_id = 'e4ebbc4b-02f0-4bc3-a0df-c57a637ac09e'"
)
txns = c.fetchall()
balance = 0.0
for tid, amt, typ, orig in txns:
    effective = orig if orig else typ
    if effective == "INCOME":
        balance += float(amt)
    else:
        balance -= float(amt)

print(f"Calculated balance for Lro: R$ {balance:.2f}")
c.execute(
    "UPDATE accounts SET balance = ? "
    "WHERE id = 'e4ebbc4b-02f0-4bc3-a0df-c57a637ac09e'",
    (balance,),
)

# Fix balance for Lro credito (credit card)
c.execute(
    "SELECT id, amount, type, original_type FROM transactions "
    "WHERE account_id = 'bea45e7b-bba2-4cfe-97a6-05ee10807bc3'"
)
txns2 = c.fetchall()
balance2 = 0.0
for tid, amt, typ, orig in txns2:
    effective = orig if orig else typ
    if effective == "INCOME":
        balance2 += float(amt)
    else:
        balance2 -= float(amt)

print(f"Calculated balance for Lro credito: R$ {balance2:.2f}")
c.execute(
    "UPDATE accounts SET balance = ? "
    "WHERE id = 'bea45e7b-bba2-4cfe-97a6-05ee10807bc3'",
    (balance2,),
)

conn.commit()

# Verify
c.execute("SELECT name, balance FROM accounts WHERE is_active = 1")
for r in c.fetchall():
    print(f"  {r[0]:<20} R$ {float(r[1]):>8.2f}")

conn.close()
