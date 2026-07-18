# AI Personal Finance Coach — Phase 1 MVP

An end-to-end pipeline that loads transaction data, cleans it, calculates
budget vs actual spend, forecasts next month's spending, and generates a
plain-English coaching insight using Gemini 2.5 Flash — exposed via a
FastAPI backend and visualized in Power BI.

## Pipeline

```
CSV (data/transactions.csv)
  -> etl/clean.py          clean + type the data
  -> db/store.py           save to SQLite (db/finance.db)
  -> budget/engine.py      budget vs actual per category/month
  -> forecast/naive.py     naive next-month forecast
  -> insights/generate.py  Gemini-generated coaching paragraph
  -> main.py               wires all of the above together
  -> api.py                exposes it as a web API (FastAPI)
  -> Power BI              dashboard on top of the exported CSVs / SQLite db
```

## Project structure

```
ai-finance-coach/
├── data/
│   └── transactions.csv       # sample dataset (swap in the real Kaggle CSV anytime)
├── etl/
│   └── clean.py
├── categorize/
│   └── rules.py                # not used yet - for uncategorized data later
├── budget/
│   └── engine.py
├── forecast/
│   └── naive.py
├── insights/
│   └── generate.py
├── db/
│   └── store.py
├── explore.py                  # one-off script to inspect the raw CSV
├── main.py                     # runs the full pipeline
├── api.py                      # FastAPI backend
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your real Gemini API key into .env
```

Get a free Gemini API key from Google AI Studio.

## Run the pipeline directly

```bash
python explore.py     # optional: sanity-check the raw data first
python main.py
```

You should see a budget table, a forecast table, and an AI-written paragraph
printed to the terminal, plus a new `db/finance.db` and two CSVs in `db/`.

## Run as a backend API

```bash
uvicorn api:app --reload
```

Open `http://127.0.0.1:8000/docs`, expand `GET /run`, click "Try it out",
then "Execute". You'll get the budget, forecast, and AI insight back as JSON.

## Connect Power BI

Get Data -> Text/CSV -> import `db/budget_vs_actual.csv` and `db/forecast.csv`.
Build a bar chart (budget vs actual by category) and a table (forecast).
Paste the AI insight text into a text box.

## Status

Phase 1 (MVP) complete: rule-based/pre-labeled categorization, naive
forecasting, single-prompt AI insight. Phase 2 will swap in ML-based
categorization and a real time-series model (Prophet/ARIMA) — same
inputs/outputs, smarter internals underneath.

## Note on the sample data

`data/transactions.csv` is a small synthetic sample (3 months, ~60 rows)
generated to match the schema of the recommended Kaggle dataset (Date,
Transaction Description, Category, Amount, Type). Swap it out for the full
downloaded dataset any time — no code changes needed as long as the column
names match.
