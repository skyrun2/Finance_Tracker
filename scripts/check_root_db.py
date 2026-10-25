import sqlite3
conn = sqlite3.connect("finance.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print([r[0] for r in c.fetchall()])
c.execute("SELECT COUNT(*) FROM imports")
print("imports:", c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM categories")
print("categories:", c.fetchone()[0])
c.execute("SELECT name, is_active FROM categories")
for r in c.fetchall():
    print(f"  {r[0]:<20} active={r[1]}")
conn.close()
