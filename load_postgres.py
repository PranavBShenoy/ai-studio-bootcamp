import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:postgres@localhost:5432/bootcamp"

df = pd.read_csv("vendor_payments.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

df["category"] = df["category"].fillna("Uncategorized")
for col in ["invoice_date", "due_date", "paid_date"]:
    df[col] = pd.to_datetime(df[col]).dt.date

engine = create_engine(DB_URL)

with engine.begin() as conn:
    with open("schema.sql") as f:
        conn.execute(text(f.read()))

df.to_sql("vendor_payments", engine, if_exists="append", index=False)

with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM vendor_payments")).scalar()
    print("Loaded rows into vendor_payments:", count)
