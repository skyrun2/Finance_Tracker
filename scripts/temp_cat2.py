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

for cat, desc, amt, date, acc in rows:
    cat_name = cat or 'Sem categoria'
    if cat_name != current_cat:
        if current_cat is not None:
            print(f'  >> Total {current_cat}: R$ {cat_totals[current_cat]:>8.2f}\n')
        current_cat = cat_name
        cat_totals[cat_name] = 0
        print(f'=== {cat_name} ===')
    cat_totals[cat_name] += float(amt)
    print(f'  R$ {float(amt):>8.2f} | {date} | {desc[:55]:55s} | {acc}')

if current_cat:
    print(f'  >> Total {current_cat}: R$ {cat_totals[current_cat]:>8.2f}')

print()
total_income = sum(v for k,v in cat_totals.items() if k in ('Investimentos',))
total_expense = sum(v for k,v in cat_totals.items() if k not in ('Investimentos', 'Sem categoria'))
print(f'TOTAL INCOME (Investimentos): R$ {total_income:.2f}')
print(f'TOTAL EXPENSE (all others):   R$ {total_expense:.2f}')
print(f'NET:                          R$ {total_income - total_expense:.2f}')
conn.close()
