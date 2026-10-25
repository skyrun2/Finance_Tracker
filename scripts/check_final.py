import sqlite3

conn = sqlite3.connect("backend/finance.db")
c = conn.cursor()

c.execute("SELECT id, name, type, is_active FROM categories ORDER BY name")
print("=== CATEGORIES ===")
for r in c.fetchall():
    print(f"  {r[1]:<20} | {r[2]:<8} | active={r[3]}")

c.execute("""
    SELECT t.id, t.description, c.name
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.category_id IS NOT NULL
    ORDER BY t.description
""")
print("\n=== CATEGORIZED TRANSACTIONS ===")
for r in c.fetchall():
    cat = r[2] or "None"
    print(f"  {r[0][:8]} | {r[1][:55]:55s} | {cat:<15}")

c.execute("SELECT COUNT(*) FROM transactions WHERE category_id IS NULL")
uncat = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM transactions")
total = c.fetchone()[0]
print(f"\nUncategorized: {uncat}/{total}")

conn.close()
