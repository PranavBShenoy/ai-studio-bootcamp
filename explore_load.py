import pandas as pd

df = pd.read_csv("vendor_payments.csv")  # update path to your synthetic CSV
print("Shape:", df.shape)
print("\nNulls:\n", df.isna().sum())
print("\nDtypes:\n", df.dtypes)
