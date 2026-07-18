"""
ETL layer: loads the raw CSV and returns a clean, typed DataFrame.
Every other module in this project depends on this running first.
"""

import pandas as pd


def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Convert the Date column from plain text into a real date type.
    # Without this, you can't group by month or sort chronologically.
    df["Date"] = pd.to_datetime(df["Date"])

    before = len(df)

    # Drop rows missing the two fields everything downstream depends on.
    df = df.dropna(subset=["Amount", "Category"])

    # Remove exact duplicate rows (can happen with export glitches).
    df = df.drop_duplicates()

    after = len(df)
    if before != after:
        print(f"[clean] Dropped {before - after} row(s) during cleaning.")

    return df


if __name__ == "__main__":
    # Lets you test this file on its own: python etl/clean.py
    df = load_and_clean("data/transactions.csv")
    print(df.head())
    print(df.dtypes)
