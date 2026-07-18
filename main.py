"""
Runs the Phase 1 pipeline: load -> clean -> store -> budget -> forecast ->
convert currency -> AI insight -> export for Power BI.

Split into two steps on purpose:
- compute_base_data(): the expensive part (reads the CSV, cleans it,
  calculates budget and forecast). Runs in the dataset's base currency.
- convert_for_display(): cheap - just multiplies by an exchange rate.

Streamlit caches the output of compute_base_data() so switching the
display currency doesn't redo the whole pipeline or re-read the CSV -
only the fast conversion step re-runs.

Run with: python main.py
"""

from etl.clean import load_and_clean
from db.store import save_to_db
from budget.engine import calculate_budget_vs_actual
from forecast.naive import forecast_next_month
from insights.generate import generate_insight
from utils.currency import CurrencyConverter


def compute_base_data():
    """Loads, cleans, and computes budget + forecast in the dataset's base
    currency. This never touches currency conversion - the numbers coming
    out of this function are the raw, unconverted values."""
    df = load_and_clean("data/transactions.csv")
    save_to_db(df)
    budget_df = calculate_budget_vs_actual(df)
    forecast_df = forecast_next_month(budget_df)
    return budget_df, forecast_df


def convert_for_display(base_budget_df, base_forecast_df, base_currency, display_currency):
    """Converts the base-currency tables into the display currency.
    Returns new DataFrames - base_budget_df/base_forecast_df are untouched."""
    budget_df = CurrencyConverter.convert_dataframe(
        base_budget_df, ["Amount", "Budget", "Difference"], base_currency, display_currency
    )
    forecast_df = CurrencyConverter.convert_dataframe(
        base_forecast_df, ["Forecasted_Next_Month"], base_currency, display_currency
    )
    return budget_df, forecast_df


def run_pipeline(base_currency: str = "USD", display_currency: str = "USD"):
    """Full end-to-end run: used by `python main.py` and by the first
    Streamlit run. Streamlit itself calls the two functions above directly
    afterwards, so it can skip re-computing base data on every currency switch.
    """
    base_budget_df, base_forecast_df = compute_base_data()
    budget_df, forecast_df = convert_for_display(
        base_budget_df, base_forecast_df, base_currency, display_currency
    )
    insight = generate_insight(
        budget_df, forecast_df, currency=CurrencyConverter.symbol(display_currency)
    )

    budget_df.to_csv("db/budget_vs_actual.csv", index=False)
    forecast_df.to_csv("db/forecast.csv", index=False)

    return budget_df, forecast_df, insight


if __name__ == "__main__":
    budget_df, forecast_df, insight = run_pipeline()

    print("\n--- Budget vs Actual ---")
    print(budget_df)

    print("\n--- Forecast (Next Month) ---")
    print(forecast_df)

    print("\n--- AI Insight ---")
    print(insight)