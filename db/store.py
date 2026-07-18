"""
Persistence layer: writes the cleaned DataFrame into a SQLite database file
so Power BI (or anything else) can query it without re-running the pipeline.
"""

import sqlite3
import pandas as pd


def save_to_db(df: pd.DataFrame, db_path: str = "db/finance.db", table_name: str = "transactions"):
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"[db] Saved {len(df)} rows to {db_path} (table: {table_name})")


def load_from_db(db_path: str = "db/finance.db", table_name: str = "transactions") -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df
