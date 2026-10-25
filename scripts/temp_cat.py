import sqlite3
conn = sqlite3.connect('finance.db')
c = conn.cursor()

c.execute("""
    SELECT c.name AS category, t.description, t.amount, t.transaction_date, a.name AS account
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    LEFT JOIN accounts a ON t.account_id = a.id
    ORDER BY c.name, t.transaction_date
""")
rows = c.fetchall()

current_cat = None
cat_totals = {}
grand_total = 0

for cat, desc, amt, date, acc in rows:
    cat_name = cat or 'Sem categoria'
    if cat_name != current_cat:
        if current_cat is not None:
            print(f'  ───────────────────────────────────────────────')
            print(f'  Total {current_cat}: R$ {cat_totals[current_cat]:>8.2f}\n')
        current_cat = cat_name
        cat_totals[cat_name] = 0
        print(f'\n=== {cat_name} ===')
    cat_totals[cat_name] += float(amt)
    print(f'  R$ {float(amt):>8.2f} | {date} | {desc[:55]:55s} | {acc}')
    grand_total += float(amt)

if current_cat:
    print(f'  ───────────────────────────────────────────────')
    print(f'  Total {current_cat}: R$ {cat_totals[current_cat]:>8.2f}')

print(f'\n{"="*60}')
print(f'GRAND TOTAL: R$ {grand_total:.2f}')
print(f'(including income as positive, expense/transfer as negative)')
print(f'{"="*60}')
conn.close()
