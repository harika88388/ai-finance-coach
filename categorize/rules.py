"""
Rules-based categorization.

Our sample dataset already has a correct 'Category' column, so this file
is NOT called by main.py right now. It's here for when you plug in your
own uncategorized transaction data (e.g. from a bank export or Option B
dataset). Phase 2 will replace this with a real ML classifier that has
the same input/output shape.
"""

CATEGORY_RULES = {
    "starbucks": "Food & Drink",
    "chipotle": "Food & Drink",
    "whole foods": "Food & Drink",
    "diner": "Food & Drink",
    "uber": "Transport",
    "shell": "Transport",
    "metro transit": "Transport",
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "amc": "Entertainment",
    "apartments": "Rent",
    "electric": "Utilities",
    "comcast": "Utilities",
    "water utility": "Utilities",
    "payroll": "Salary",
    "vanguard": "Investment",
}


def categorize(description: str) -> str:
    description = str(description).lower()
    for keyword, category in CATEGORY_RULES.items():
        if keyword in description:
            return category
    return "Uncategorized"


def categorize_dataframe(df, description_col="Transaction Description"):
    """Apply categorize() to every row and return the updated DataFrame."""
    df = df.copy()
    df["Category"] = df[description_col].apply(categorize)
    return df
