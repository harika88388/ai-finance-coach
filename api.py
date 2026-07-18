"""
FastAPI backend: exposes the pipeline as a web API so it can be demoed
or connected to a frontend without running main.py by hand.

Run with: uvicorn api:app --reload
Then open: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from main import run_pipeline

app = FastAPI(title="AI Personal Finance Coach")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Finance Coach API is running"}


@app.get("/run")
def run():
    budget_df, forecast_df, insight = run_pipeline()
    return {
        "budget": budget_df.to_dict(orient="records"),
        "forecast": forecast_df.to_dict(orient="records"),
        "insight": insight,
    }
