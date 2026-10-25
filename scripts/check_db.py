import sqlite3

root = sqlite3.connect("finance.db")
c = root.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Root finance.db tables:", tables)
try:
    c.execute("SELECT COUNT(*) FROM categories")
    print("Root categories:", c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM transactions")
    print("Root transactions:", c.fetchone()[0])
except Exception as e:
    print("Root error:", e)
root.close()

be = sqlite3.connect("backend/finance.db")
c = be.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Backend finance.db tables:", tables)
try:
    c.execute("SELECT COUNT(*) FROM categories")
    print("Backend categories:", c.fetchone()[0])
    c.execute("SELECT id, description, category_id FROM transactions LIMIT 5")
    for r in c.fetchall():
        print(f"  txn: {r[0][:8]} | {r[1][:40]:40s} | cat_id={r[2]}")
    c.execute("SELECT COUNT(*) FROM transactions")
    print("Backend transactions:", c.fetchone()[0])
except Exception as e:
    print("Backend error:", e)
be.close()
