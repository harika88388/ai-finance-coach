"""
AI insight agent: turns the budget + forecast tables into a short,
plain-English coaching paragraph using Gemini 2.5 Flash.

Requires GOOGLE_API_KEY to be set as an environment variable
(see .env.example). Uses the current "google-genai" SDK
(the old "google-generativeai" package is deprecated).
"""

import pandas as pd
from google import genai
from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present

# Client() automatically reads GOOGLE_API_KEY (or GEMINI_API_KEY) from
# the environment - no need to pass it in manually.
client = genai.Client()


def generate_insight(budget_df: pd.DataFrame, forecast_df: pd.DataFrame, currency: str = "$") -> str:
    prompt = f"""
You are a personal finance coach. All amounts below are in the currency symbol "{currency}".

Budget vs actual spending:
{budget_df.to_string(index=False)}

Forecasted spending next month:
{forecast_df.to_string(index=False)}

Respond in EXACTLY this format. Use these four section headers, each on its own
line, in this exact order, with nothing before the first header:

📌 Key Insight
One to two sentences on the single most important thing that happened, with exact {currency} amounts.

💡 Recommendation
One concrete, specific action for next month. Not generic advice like "spend less."

💰 Potential Savings
The exact {currency} amount they could save next month, and the annualized amount if kept up.

⚠ Priority
One word - High, Medium, or Low - followed by a five-word reason.

Keep each section to 1-2 short sentences. Be warm, specific, and practical - no filler.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text