"""
Naive forecast: predicts next month's spend per category as the average
of past months. Intentionally simple - Phase 2 replaces this with
Prophet/ARIMA. This just proves the "forecast" slot in the pipeline works.
"""

import pandas as pd


def forecast_next_month(monthly_budget_df: pd.DataFrame) -> pd.DataFrame:
    avg_by_category = (
        monthly_budget_df.groupby("Category")["Amount"]
        .mean()
        .reset_index()
        .rename(columns={"Amount": "Forecasted_Next_Month"})
    )
    return avg_by_category
