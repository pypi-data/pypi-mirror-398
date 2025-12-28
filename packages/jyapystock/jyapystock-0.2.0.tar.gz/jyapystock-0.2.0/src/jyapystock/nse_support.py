"""
NSE (National Stock Exchange of India) support for jyapystock.
Provides helper functions to fetch live and historical prices for Indian stocks.
"""

from nse import NSE
import tempfile
from typing import Optional, Union
from datetime import datetime
from dateutil.parser import parse


# Global NSE instance
_nse_instance = None


def _get_nse_instance():
    """Get or create a singleton NSE instance."""
    global _nse_instance
    if _nse_instance is None:
        temp_dir = tempfile.mkdtemp()
        _nse_instance = NSE(download_folder=temp_dir)
    return _nse_instance


def get_nse_live_price(symbol: str) -> Optional[dict]:
    """
    Fetch live quote for an Indian stock using NSE API.
    
    Returns a dict with 'timestamp', 'price', and 'change_percent', or None if not available.
    """
    try:
        nse = _get_nse_instance()
        # equityQuote returns simple data, quote returns detailed data
        result = nse.quote(symbol)
        
        if not result or 'priceInfo' not in result:
            return None
        
        price_info = result['priceInfo']
        last_price = price_info.get('lastPrice')
        change = price_info.get('change', 0)
        p_change = price_info.get('pChange', 0)  # percentage change
        
        metadata = result.get('metadata', {})
        timestamp = metadata.get('lastUpdateTime', '')
        
        if last_price is None:
            return None
        
        return {
            "timestamp": timestamp,
            "price": last_price,
            "change_percent": round(p_change, 2)
        }
    except Exception:
        return None


def get_nse_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime]) -> Optional[list]:
    """
    Fetch historical prices for an Indian stock from NSE.
    
    `start` and `end` may be strings (ISO like '2023-01-01') or datetime objects.
    Returns a list of records with date/open/high/low/close/volume, or None if not available.
    """
    try:
        # Normalize start/end to date strings
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
        
        nse = _get_nse_instance()
        # fetch_equity_historical_data returns historical data
        data = nse.fetch_equity_historical_data(symbol, start_date=str(start_dt), end_date=str(end_dt))
        
        if not data or isinstance(data, str):
            # Data might be an error string or None
            return None
        
        # NSE returns a DataFrame or dict; normalize to list of dicts
        records = []
        if hasattr(data, 'to_dict'):
            # It's a pandas DataFrame
            for idx, row in data.iterrows():
                records.append({
                    'date': str(row.get('Date', idx)),
                    'Open': row.get('Open'),
                    'High': row.get('High'),
                    'Low': row.get('Low'),
                    'Close': row.get('Close'),
                    'Volume': row.get('Volume')
                })
        elif isinstance(data, dict):
            # Already a dict
            records.append(data)
        else:
            # List of records
            records = list(data) if hasattr(data, '__iter__') else [data]
        
        return records if records else None
    except Exception:
        return None
