"""
NASDAQ support for jyapystock.
Provides helper functions to fetch live and historical prices from Nasdaq's public API.
"""
import requests
from datetime import datetime
from typing import Optional, Union
from dateutil.parser import parse


def get_nasdaq_live_price(symbol: str, country: str) -> Optional[dict]:
    """
    Returns a dict with 'timestamp', 'price', and 'change_percent', or None if not available.
    """
    if country != "usa":
        return None  # NASDAQ support only for USA
    headers =  {
                    'Accept': 'application/json, text/plain, */*',
                    'DNT': "1",
                    'Origin': 'https://www.nasdaq.com/',
                    'Sec-Fetch-Mode': 'cors',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'
                }
    url_stocks = f"https://api.nasdaq.com/api/quote/{symbol}/info?assetclass=stocks"
    url_etf = f"https://api.nasdaq.com/api/quote/{symbol}/info?assetclass=etf"
    for url in [url_stocks, url_etf]:
        try:
            get_response = requests.get(url, headers=headers, timeout=10)
            if get_response and get_response.status_code == 200:
                json_data = get_response.json()
                if 'data' in json_data and json_data['data']:
                    data_block = json_data['data']
                    # Prefer secondaryData lastSalePrice if present
                    sec = data_block.get('secondaryData')
                    if sec and sec.get('lastSalePrice'):
                        try:
                            price = float(sec['lastSalePrice'].replace('$', '').replace(',', ''))
                            # Try to get change percent from secondaryData
                            change_str = sec.get('change', '0')
                            change_percent = float(change_str) if change_str else 0.0
                            return {
                                "timestamp": sec.get('lastTradeTimestamp', ''),
                                "price": price,
                                "change_percent": round(change_percent, 2)
                            }
                        except Exception:
                            pass

                    prim = data_block.get('primaryData')
                    if prim and prim.get('lastSalePrice'):
                        try:
                            price = float(prim['lastSalePrice'].replace('$', '').replace(',', ''))
                            # Try to get change percent from primaryData
                            change_str = prim.get('change', '0')
                            change_percent = float(change_str) if change_str else 0.0
                            return {
                                "timestamp": prim.get('lastTradeTimestamp', ''),
                                "price": price,
                                "change_percent": round(change_percent, 2)
                            }
                        except Exception:
                            pass
        except Exception:
            continue
    return None


def get_nasdaq_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime], country: str) -> Optional[list]:
    """
    Returns a list of records with Open/High/Low/Close/Volume or None if not found.
    """
    if country != "usa":
        return None  # NASDAQ support only for USA
    # Normalize start/end to datetime if they are strings
    try:
        if isinstance(start, str):
            start = parse(start)
        if isinstance(end, str):
            end = parse(end)
    except Exception:
        # If parsing fails, leave as-is and let later formatting raise if necessary
        pass
    # Build URLs for stocks and ETFs
    url_stocks = f"https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass=stocks&fromdate={start.strftime('%Y-%m-%d')}&limit=9999&todate={end.strftime('%Y-%m-%d')}"
    url_etf = f"https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass=etf&fromdate={start.strftime('%Y-%m-%d')}&limit=9999&todate={end.strftime('%Y-%m-%d')}"

    headers = {
                'Content-Type': "application/x-www-form-urlencoded",
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
                'Accept': "application/json, text/plain, */*",
                'Origin': "https://www.nasdaq.com",
                'accept-encoding': "gzip, deflate, br",
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': "close",
                'cache-control': "no-cache",
                'Referer': 'https://www.nasdaq.com/'
            }

    for url in [url_stocks, url_etf]:
        try:
            get_response = requests.get(url, headers=headers, timeout=10)
            if get_response and get_response.status_code == 200:
                json_data = get_response.json()
                if 'data' in json_data and 'tradesTable' in json_data['data']:
                    rows = json_data['data']['tradesTable']['rows']
                    records = []
                    for row in rows:
                        try:
                            cdate = datetime.strptime(row.get('date', ''), '%m/%d/%Y').date()
                            close = get_float_or_none_from_string(row.get('close'))
                            open_v = get_float_or_none_from_string(row.get('open'))
                            high = get_float_or_none_from_string(row.get('high'))
                            low = get_float_or_none_from_string(row.get('low'))
                            vol_raw = row.get('volume')
                            volume = None
                            if vol_raw:
                                try:
                                    volume = int(str(vol_raw).replace(',', '').strip())
                                except Exception:
                                    volume = None

                            records.append({
                                'date': str(cdate),
                                'Open': open_v,
                                'High': high,
                                'Low': low,
                                'Close': close,
                                'Volume': volume
                            })
                        except Exception:
                            continue

                    return records
        except Exception:
            continue

    return None
    
def get_float_or_none_from_string(input):
    if input != None and input != '':
        try:
            input = input.replace(',', '')
            input = input.replace('$', '')
            input = input.strip()
            res = float(input)
            return res
        except Exception as e:
            pass
    return None
