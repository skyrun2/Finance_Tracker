import sqlite3
conn = sqlite3.connect("backend/finance.db")
c = conn.cursor()

print("=== Accounts ===")
c.execute("SELECT id, name, type, balance FROM accounts WHERE is_active = 1")
for r in c.fetchall():
    print(f"  {r[0][:8]} | {r[1]:<20} | {r[2]:<12} | R$ {float(r[3]):>8.2f}")

print("\n=== Lro - Total por tipo ===")
c.execute("SELECT type, original_type, SUM(amount) FROM transactions WHERE account_id = 'e4ebbc4b-02f0-4bc3-a0df-c57a637ac09e' GROUP BY type, original_type ORDER BY type")
for r in c.fetchall():
    orig = r[1] or "—"
    print(f"  type={r[0]:<10} orig={orig:<10} total=R$ {float(r[2]):>8.2f}")

print("\n=== Lro credito - Total por tipo ===")
c.execute("SELECT type, original_type, SUM(amount) FROM transactions WHERE account_id = 'bea45e7b-bba2-4cfe-97a6-05ee10807bc3' GROUP BY type, original_type ORDER BY type")
for r in c.fetchall():
    orig = r[1] or "—"
    print(f"  type={r[0]:<10} orig={orig:<10} total=R$ {float(r[2]):>8.2f}")

print("\n=== Income transactions ===")
c.execute("SELECT description, amount FROM transactions WHERE account_id = 'e4ebbc4b-02f0-4bc3-a0df-c57a637ac09e' AND (type = 'INCOME' OR original_type = 'INCOME') ORDER BY amount DESC")
for r in c.fetchall():
    print(f"  +R$ {float(r[1]):>8.2f} | {r[0][:50]}")

conn.close()
