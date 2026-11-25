import random
from datetime import date, timedelta
import pandas as pd

random.seed(42)
vendors = [
    ("V001", "Apex Cloud Systems", "Cloud"),
    ("V002", "Kaveri Office Supplies", "Operations"),
    ("V003", "Nitte Logistics Pvt Ltd", "Logistics"),
    ("V004", "Zenith Security Labs", "Security"),
    ("V005", "Malnad Industrial Tools", "Hardware"),
    ("V006", "Coastal Print & Media", "Marketing"),
]
statuses = ["Paid", "Pending", "Overdue"]
rows = []
base_date = date(2026, 8, 1)

for i in range(1, 121):
    vid, vname, cat = random.choice(vendors)
    invoice_date = base_date + timedelta(days=random.randint(0, 105))
    due_date = invoice_date + timedelta(days=30)
    status = random.choices(statuses, weights=[0.7, 0.15, 0.15])[0]
    if status == "Paid":
        paid_date = due_date + timedelta(days=random.randint(-5, 14))
    elif status == "Overdue":
        paid_date = None
    else:
        paid_date = None

    amount = round(random.uniform(1500, 95000), 2)
    if i % 25 == 0:
        amount = round(amount * 3.5, 2)  # outlier invoice
    if i % 19 == 0:
        cat = None  # intentional null for Step 1 exploration

    rows.append({
        "payment_id": i,
        "vendor_id": vid,
        "vendor_name": vname,
        "category": cat,
        "invoice_number": f"INV-{1000 + i}",
        "invoice_date": invoice_date.isoformat(),
        "due_date": due_date.isoformat(),
        "paid_date": paid_date.isoformat() if paid_date else None,
        "amount": amount,
        "status": status,
    })

# Add intentional duplicate invoice payments for window function / HAVING queries
for dup_idx in [5, 18, 42]:
    dup = dict(rows[dup_idx])
    dup["payment_id"] = len(rows) + 1
    dup["paid_date"] = (date.fromisoformat(dup["due_date"]) + timedelta(days=2)).isoformat()
    dup["status"] = "Paid"
    rows.append(dup)

pd.DataFrame(rows).to_csv("vendor_payments.csv", index=False)
print("Generated vendor_payments.csv with", len(rows), "rows")
