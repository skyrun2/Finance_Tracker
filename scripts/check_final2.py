import sqlite3
conn = sqlite3.connect("finance.db")
c = conn.cursor()

c.execute("SELECT c.name, COUNT(t.id) FROM transactions t LEFT JOIN categories c ON t.category_id = c.id GROUP BY c.name ORDER BY COUNT(*) DESC")
print("=== TRANSACTIONS BY CATEGORY ===")
for r in c.fetchall():
    print(f"  {r[0] or 'None':<20} | {r[1]}")

c.execute("SELECT t.description, c.name FROM transactions t LEFT JOIN categories c ON t.category_id = c.id ORDER BY t.description")
print("\n=== ALL TRANSACTIONS ===")
for r in c.fetchall():
    cat = r[1] or "—"
    print(f"  {r[0][:55]:55s} | {cat}")

conn.close()
