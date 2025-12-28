"""
yfinance support for jyapystock
Provides helper functions to fetch live and historical prices using yfinance
and to try country-specific symbol variants (e.g., .NS/.BO for India).
"""

from datetime import datetime
from typing import Optional, Union
import yfinance as yf
from dateutil.parser import parse


def get_yfinance_live_price(symbol: str, country: str) -> Optional[dict]:
    """Try live price with possible symbol variants for the given country.

    Returns a dict with 'timestamp', 'price', and 'change_percent' (% change from previous day close),
    or None if not available.
    """
    variants = [symbol]
    if country == "india":
        if "." not in symbol:
            variants = [f"{symbol}.NS", f"{symbol}.BO", symbol]

    for s in variants:
        try:
            ticker = yf.Ticker(s)
            # Get last 2 days of data to compute % change
            data = ticker.history(period="2d")
            if not data.empty:
                last_close = float(data["Close"].iloc[-1])
                prev_close = float(data["Close"].iloc[-2]) if len(data) > 1 else last_close
                change_percent = ((last_close - prev_close) / prev_close * 100) if prev_close != 0 else 0.0
                timestamp = data.index[-1].isoformat() if hasattr(data.index[-1], 'isoformat') else str(data.index[-1])
                return {
                    "timestamp": timestamp,
                    "price": last_close,
                    "change_percent": round(change_percent, 2)
                }
        except Exception:
            continue
    return None


def get_yfinance_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime], country: str) -> Optional[list]:
    """Try historical price retrieval with symbol variants.

    Returns a list of records with Open/High/Low/Close/Volume or None if not found.
    """
    variants = [symbol]
    if country == "india":
        if "." not in symbol:
            variants = [f"{symbol}.NS", f"{symbol}.BO", symbol]
    # Normalize start/end if strings are passed
    try:
        start_dt = parse(start) if isinstance(start, str) else start
    except Exception:
        start_dt = start
    try:
        end_dt = parse(end) if isinstance(end, str) else end
    except Exception:
        end_dt = end
    for s in variants:
        try:
            ticker = yf.Ticker(s)
            data = ticker.history(start=start_dt, end=end_dt)
            if not data.empty:
                # Ensure dates are included in the records
                df = data.reset_index()
                df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
                return df.to_dict("records")
        except Exception:
            continue
    return None
