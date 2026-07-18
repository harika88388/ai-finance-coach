"""
Throwaway exploration script - run this first, before touching any other
file, to confirm the raw CSV loads correctly and see its real shape.

Run with: python explore.py
"""

import pandas as pd

df = pd.read_csv("data/transactions.csv")

print("--- First 5 rows ---")
print(df.head())

print("\n--- Column data types ---")
print(df.dtypes)

print("\n--- Missing values per column ---")
print(df.isnull().sum())
