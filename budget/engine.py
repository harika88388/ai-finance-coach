"""
Budget engine: compares actual monthly spend per category against a
budget limit. This produces the core numeric table the AI insight step
will later turn into plain English.
"""

import pandas as pd

BUDGET_LIMITS = {
    "Food & Drink": 400,
    "Rent": 1200,
    "Entertainment": 100,
    "Transport": 150,
    "Utilities": 200,
}


def calculate_budget_vs_actual(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    expenses = df[df["Type"] == "Expense"]

    monthly = (
        expenses.groupby(["Month", "Category"])["Amount"]
        .sum()
        .reset_index()
    )

    monthly["Budget"] = monthly["Category"].map(BUDGET_LIMITS)
    monthly["Difference"] = monthly["Budget"] - monthly["Amount"]

    return monthly


if __name__ == "__main__":
    from etl.clean import load_and_clean
    df = load_and_clean("data/transactions.csv")
    print(calculate_budget_vs_actual(df))
