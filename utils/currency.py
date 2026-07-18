"""
Single source of truth for currency symbols, live exchange rates, and
conversion logic. Every part of the app (pipeline, AI prompt, Streamlit
display) routes through CurrencyConverter - nothing converts or formats
currency on its own.

Live rates come from open.er-api.com (free, no API key required, updated
daily). If that request fails for any reason (offline, API down, timeout),
we fall back to a static offline rate table so the app never crashes -
it just tells you it's using an offline rate instead of a live one.
"""

import time
import requests
import pandas as pd


class CurrencyConverter:
    API_URL = "https://open.er-api.com/v6/latest/{base}"
    REQUEST_TIMEOUT_SECONDS = 5
    CACHE_TTL_SECONDS = 3600  # re-fetch live rates at most once an hour

    SYMBOLS = {
        "USD": "$",
        "INR": "₹",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }

    # Used ONLY if the live API call fails. Approximate, for offline demo use.
    FALLBACK_RATES_TO_USD = {
        "USD": 1.0,
        "INR": 83.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 156.0,
    }

    # Yen has no minor unit in normal use - 0 decimal places, not 2.
    DECIMAL_PLACES = {"JPY": 0}
    DEFAULT_DECIMAL_PLACES = 2

    _rate_cache = {}  # {base_currency: {"rates": {...}, "fetched_at": timestamp}}

    # ---------- Rate lookup ----------

    @classmethod
    def _fetch_live_rates(cls, base_currency: str) -> dict:
        """Returns {currency_code: rate} for the given base, using a short-lived
        cache so we don't hit the API on every Streamlit rerun."""
        cached = cls._rate_cache.get(base_currency)
        if cached and (time.time() - cached["fetched_at"] < cls.CACHE_TTL_SECONDS):
            return cached["rates"]

        response = requests.get(
            cls.API_URL.format(base=base_currency), timeout=cls.REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success":
            raise ValueError(f"Exchange rate API did not return success: {data}")

        cls._rate_cache[base_currency] = {"rates": data["rates"], "fetched_at": time.time()}
        return data["rates"]

    @classmethod
    def get_rate(cls, from_currency: str, to_currency: str):
        """Returns (rate, source) where source is 'live' or 'fallback'."""
        if from_currency == to_currency:
            return 1.0, "live"

        try:
            rates = cls._fetch_live_rates(from_currency)
            return rates[to_currency], "live"
        except Exception:
            from_usd = cls.FALLBACK_RATES_TO_USD.get(from_currency)
            to_usd = cls.FALLBACK_RATES_TO_USD.get(to_currency)
            if from_usd is None or to_usd is None:
                raise ValueError(f"No rate available for {from_currency} -> {to_currency}")
            return to_usd / from_usd, "fallback"

    # ---------- Conversion ----------

    @classmethod
    def convert(cls, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency or pd.isna(amount):
            return amount
        rate, _ = cls.get_rate(from_currency, to_currency)
        return amount * rate

    @classmethod
    def convert_dataframe(cls, df: pd.DataFrame, amount_columns: list,
                           from_currency: str, to_currency: str) -> pd.DataFrame:
        """Returns a NEW DataFrame with the given columns converted.
        The original df passed in is never modified - this is what keeps
        the raw dataset untouched while only the display changes."""
        if from_currency == to_currency:
            return df.copy()

        rate, _ = cls.get_rate(from_currency, to_currency)
        out = df.copy()
        for col in amount_columns:
            if col in out.columns:
                out[col] = out[col] * rate
        return out

    # ---------- Formatting ----------

    @classmethod
    def symbol(cls, currency_code: str) -> str:
        return cls.SYMBOLS.get(currency_code, currency_code)

    @classmethod
    def format_amount(cls, amount: float, currency_code: str) -> str:
        if pd.isna(amount):
            return "-"
        decimals = cls.DECIMAL_PLACES.get(currency_code, cls.DEFAULT_DECIMAL_PLACES)
        return f"{cls.symbol(currency_code)}{amount:,.{decimals}f}"

    @classmethod
    def number_format_spec(cls, currency_code: str) -> str:
        """Printf-style format string for Streamlit's column_config.NumberColumn."""
        decimals = cls.DECIMAL_PLACES.get(currency_code, cls.DEFAULT_DECIMAL_PLACES)
        return f"{cls.symbol(currency_code)}%.{decimals}f"

    @classmethod
    def rate_caption(cls, from_currency: str, to_currency: str) -> str:
        """A one-line disclosure string for the UI."""
        if from_currency == to_currency:
            return ""
        rate, source = cls.get_rate(from_currency, to_currency)
        if source == "live":
            return f"Live rate: 1 {from_currency} ≈ {rate:,.2f} {to_currency}"
        return (f"⚠ Live exchange rate API unreachable — using an offline fallback rate: "
                f"1 {from_currency} ≈ {rate:,.2f} {to_currency}")