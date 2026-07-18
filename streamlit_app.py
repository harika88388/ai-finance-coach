"""
Streamlit frontend for the AI Personal Finance Coach.

Run with: streamlit run streamlit_app.py
Then it opens automatically at http://localhost:8501
"""

import re
import streamlit as st
from main import compute_base_data, convert_for_display
from insights.generate import generate_insight
from utils.currency import CurrencyConverter

st.set_page_config(page_title="AI Personal Finance Coach", page_icon="💰", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 780px; }
h2, h3 { margin-top: 1.8rem !important; }
[data-testid="stMetric"] {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 10px;
    padding: 0.9rem 1rem;
}
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.4rem;
}
hr { margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


def parse_insight(text: str) -> dict:
    labels = ["📌 Key Insight", "💡 Recommendation", "💰 Potential Savings", "⚠ Priority"]
    pattern = "(" + "|".join(re.escape(l) for l in labels) + ")"
    parts = re.split(pattern, text)
    result, current = {}, None
    for part in parts:
        part = part.strip()
        if part in labels:
            current, result[current] = part, ""
        elif current:
            result[current] += part
    return result if len(result) == 4 else {}


@st.cache_data(show_spinner=False)
def cached_base_data():
    """The expensive part: read + clean the CSV, calculate budget and
    forecast in the dataset's base currency. Cached so switching the
    display currency later doesn't redo this - only the cheap conversion
    step and the AI call re-run."""
    return compute_base_data()


CURRENCY_CODES = list(CurrencyConverter.SYMBOLS.keys())

with st.sidebar:
    st.header("Settings")
    base_currency = st.selectbox(
        "Base currency (your data)", CURRENCY_CODES, index=0,
        help="What currency the amounts in transactions.csv are actually recorded in.",
    )
    display_currency = st.selectbox(
        "Display currency", CURRENCY_CODES, index=0,
        help="What currency to show everywhere - tables, charts, and AI insights. Fetched live.",
    )
    run_clicked = st.button("Run pipeline", type="primary", use_container_width=True)
    st.caption("Cleans your data, calculates budget vs actual, forecasts next month, and asks your AI coach for advice.")

currency = CurrencyConverter.symbol(display_currency)

st.title("💰 AI Personal Finance Coach")
st.caption("Your weekly check-in on spending, budget, and savings.")

if run_clicked:
    with st.spinner("Crunching numbers and asking your coach..."):
        base_budget_df, base_forecast_df = cached_base_data()
        budget_df, forecast_df = convert_for_display(
            base_budget_df, base_forecast_df, base_currency, display_currency
        )
        insight = generate_insight(budget_df, forecast_df, currency=currency)

        budget_df.to_csv("db/budget_vs_actual.csv", index=False)
        forecast_df.to_csv("db/forecast.csv", index=False)

    disclosure = CurrencyConverter.rate_caption(base_currency, display_currency)
    if disclosure:
        if disclosure.startswith("⚠"):
            st.warning(disclosure)
        else:
            st.caption(f"ℹ️ {disclosure}")

    num_format = CurrencyConverter.number_format_spec(display_currency)

    latest_month = budget_df["Month"].max()
    latest = budget_df[budget_df["Month"] == latest_month]

    total_spent = latest["Amount"].sum()
    total_budget = latest["Budget"].sum(skipna=True)
    net = total_budget - total_spent

    overspent = latest[latest["Difference"] < 0]
    potential_savings = -overspent["Difference"].sum() if not overspent.empty else 0

    st.subheader(f"Snapshot — {latest_month}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Spent", CurrencyConverter.format_amount(total_spent, display_currency))
    col2.metric("Budgeted", CurrencyConverter.format_amount(total_budget, display_currency))
    col3.metric(
        "Under / over",
        CurrencyConverter.format_amount(net, display_currency),
        delta=CurrencyConverter.format_amount(net, display_currency),
    )

    if potential_savings > 0:
        st.warning(
            f"Bring over-budget categories back in line and you could free up "
            f"**{CurrencyConverter.format_amount(potential_savings, display_currency)}** next month."
        )
    else:
        st.success("Every category is within budget this month. Nice work.")

    st.divider()

    st.subheader("Budget vs actual, by category")
    left, right = st.columns([3, 2])
    with left:
        st.dataframe(
            budget_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn("Spent", format=num_format),
                "Budget": st.column_config.NumberColumn("Budget", format=num_format),
                "Difference": st.column_config.NumberColumn("Under/Over", format=num_format),
            },
        )
    with right:
        chart_data = latest.set_index("Category")[["Amount", "Budget"]]
        st.bar_chart(chart_data, height=280)

    st.divider()

    st.subheader("Coach's notes")
    warn_col, win_col = st.columns(2)

    with warn_col:
        st.markdown("**Needs attention**")
        if overspent.empty:
            st.caption("Nothing over budget this month.")
        for _, row in overspent.iterrows():
            over_amt = -row["Difference"]
            with st.container(border=True):
                st.markdown(f"**{row['Category']}**")
                st.caption(
                    f"{CurrencyConverter.format_amount(over_amt, display_currency)} over "
                    f"({CurrencyConverter.format_amount(row['Amount'], display_currency)} of "
                    f"{CurrencyConverter.format_amount(row['Budget'], display_currency)})"
                )

    with win_col:
        st.markdown("**Doing well**")
        under = latest[latest["Difference"] > 0].sort_values("Difference", ascending=False)
        if under.empty:
            st.caption("No categories under budget this month.")
        for _, row in under.head(2).iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Category']}**")
                st.caption(f"{CurrencyConverter.format_amount(row['Difference'], display_currency)} under budget")

    st.divider()

    st.subheader("Forecast for next month")
    st.dataframe(
        forecast_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Forecasted_Next_Month": st.column_config.NumberColumn("Forecasted spend", format=num_format)
        },
    )

    st.divider()

    st.subheader("🤖 Your AI coach")
    sections = parse_insight(insight)

    if sections:
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("**📌 Key insight**")
                st.write(sections.get("📌 Key Insight", "").strip())
        with c2:
            with st.container(border=True):
                st.markdown("**💡 Recommendation**")
                st.write(sections.get("💡 Recommendation", "").strip())

        c3, c4 = st.columns(2)
        with c3:
            with st.container(border=True):
                st.markdown("**💰 Potential savings**")
                st.write(sections.get("💰 Potential Savings", "").strip())
        with c4:
            with st.container(border=True):
                st.markdown("**⚠ Priority**")
                st.write(sections.get("⚠ Priority", "").strip())
    else:
        st.info(insight)
else:
    st.info("Click **Run pipeline** in the sidebar to get your snapshot.")