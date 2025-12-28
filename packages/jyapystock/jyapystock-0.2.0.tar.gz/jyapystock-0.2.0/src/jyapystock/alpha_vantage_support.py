"""Alpha Vantage support for jyapystock
Provides live and historical fetchers. Historical function accepts
`start` and `end` as either `str` (ISO date) or `datetime` and normalizes them.
"""
import os
import requests
from typing import Union
from datetime import datetime
from dateutil.parser import parse


def get_alpha_vantage_live_price(symbol: str, api_key: str) -> dict:
    """Fetch live quote data including price and change percent.
    
    Returns a dict with 'timestamp', 'price', and 'change_percent', or None if not available.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception:
        return None
    try:
        quote = data["Global Quote"]
        price = float(quote["05. price"])
        # Alpha Vantage provides change_percent directly
        change_percent_str = quote.get("10. change percent", "0%")
        # Parse percentage string (e.g., "1.23%" -> 1.23)
        change_percent = float(change_percent_str.rstrip('%')) if change_percent_str else 0.0
        timestamp = quote.get("07. latest trading day", "")
        return {
            "timestamp": timestamp,
            "price": price,
            "change_percent": round(change_percent, 2)
        }
    except Exception:
        return None


def get_alpha_vantage_historical_price(symbol: str, start: Union[str, datetime], end: Union[str, datetime], api_key: str) -> list:
    """Fetch historical daily-adjusted data and return list of records.

    `start` and `end` may be strings (ISO like '2023-01-01') or datetime objects.
    """
    # Normalize start/end to ISO date strings
    try:
        if isinstance(start, str):
            start_dt = parse(start).date()
        elif isinstance(start, datetime):
            start_dt = start.date()
        else:
            start_dt = start

        if isinstance(end, str):
            end_dt = parse(end).date()
        elif isinstance(end, datetime):
            end_dt = end.date()
        else:
            end_dt = end
    except Exception:
        # If parsing fails, fall back to raw comparison later
        start_dt = start
        end_dt = end

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}"
    try:
        resp = requests.get(url, timeout=20)
        data = resp.json()
    except Exception:
        return None
    prices = []
    try:
        ts = data["Time Series (Daily)"]
        for date_str, values in ts.items():
            try:
                date_obj = parse(date_str).date()
            except Exception:
                continue

            # Compare using date objects when possible
            if (isinstance(start_dt, datetime) or hasattr(start_dt, 'isoformat')):
                in_range = (start_dt <= date_obj <= end_dt)
            else:
                # fallback to string comparison
                in_range = (str(start) <= date_str <= str(end))

            if in_range:
                prices.append({
                    "date": date_str,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["6. volume"])
                })
        prices.sort(key=lambda x: x["date"])
        return prices
    except Exception:
        return []
