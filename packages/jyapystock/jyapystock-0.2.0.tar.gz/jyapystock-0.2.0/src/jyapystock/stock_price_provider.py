"""
jyapystock: Stock price library supporting live and historical prices for Indian and American stocks.
Sources: yfinance (default), Alpha Vantage (optional)
"""

from datetime import datetime
from typing import Optional, Union
import os
from jyapystock.alpha_vantage_support import get_alpha_vantage_live_price, get_alpha_vantage_historical_price
from jyapystock.yfinance_support import get_yfinance_live_price, get_yfinance_historical_prices
from jyapystock.nasdaq_support import get_nasdaq_live_price, get_nasdaq_historical_prices
from jyapystock.nse_support import get_nse_live_price, get_nse_historical_prices

class StockPriceProvider:
    def __init__(self, country: str, source: Optional[str] = None, alpha_vantage_api_key: Optional[str] = None):
        """Create a provider.

        If `source` is None or 'auto', the provider will try available free sources
        in order (yfinance first, then Alpha Vantage if an API key is provided).
        Otherwise specify `source` as 'yfinance' or 'alphavantage'.
        """
        self.country = country.lower()
        self.check_country_validity()
        if source:
            self.source = source.lower()
        else:
            self.source = "auto"
        self.check_source_validity()
        self.alpha_vantage_api_key = alpha_vantage_api_key

    def check_source_validity(self):
        """Check if the provided source is valid."""
        valid_sources = ["yfinance", "alphavantage", "nasdaq", "nse", "auto"]
        if self.source not in valid_sources:
            raise ValueError(f"Unknown source: {self.source}. Valid options are: {valid_sources}")

    def check_country_validity(self):
        """Check if the provided country is valid."""
        valid_countries = ["india", "usa"]
        if self.country not in valid_countries:
            raise ValueError(f"Unknown country: {self.country}. Valid options are: {valid_countries}")
    
    def get_live_price(self, symbol: str) -> Optional[dict]:
        """
        Get the live price for the given symbol.
        :param symbol: Symbol to fetch the live price for
        :type symbol: str
        :return: Returns a dict with 'timestamp', 'price', and 'change_percent' (% change from previous day close),
                 or None if not available.
        :rtype: dict | None
        """
        if self.source == "yfinance" or self.source == "auto":
            # Try yfinance first (free), respecting country-specific variants
            val = get_yfinance_live_price(symbol, self.country)
            if val is not None:
                return val
        
        # Try NSE for India stocks
        if (self.source == "nse" or self.source == "auto") and self.country == "india":
            val = get_nse_live_price(symbol)
            if val is not None:
                return val
        
        # Try NASDAQ-specific provider for USA symbols
        if (self.source == "nasdaq" or self.source == "auto") and self.country == "usa":
            val = get_nasdaq_live_price(symbol, self.country)
            if val is not None:
                return val
        
        if self.source == "alphavantage" or self.source == "auto":
            # Try Alpha Vantage if API key available
            av_key = self.alpha_vantage_api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
            if av_key:
                val = get_alpha_vantage_live_price(symbol, av_key)
                if val is not None:
                    return val

        # No sources returned a price
        return None

    def get_historical_price(self, symbol: str, start: Union[str, datetime], end: Union[str, datetime]) -> Optional[list]:
        # Auto mode: try yfinance first, then NSE for India, then Alpha Vantage if available
        if self.source == "yfinance" or self.source == "auto":
            # Try yfinance first (respecting country-specific variants)
            val = get_yfinance_historical_prices(symbol, start, end, self.country)
            if val is not None:
                return val
        
        # NSE for India stocks
        if (self.source == "nse" or self.source == "auto") and self.country == "india":
            val = get_nse_historical_prices(symbol, start, end)
            if val is not None:
                return val
        
        # NASDAQ historical provider (USA)
        if (self.source == "nasdaq" or self.source == "auto") and self.country == "usa":
            val = get_nasdaq_historical_prices(symbol, start, end, self.country)
            if val is not None:
                return val
        
        if self.source == "alphavantage" or self.source == "auto":
            av_key = self.alpha_vantage_api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
            if av_key:
                val = get_alpha_vantage_historical_price(symbol, start, end, av_key)
                if val is not None:
                    return val

        return None


# Example usage:
# provider = StockPriceProvider()
# price = provider.get_live_price("AAPL")
# price_in = provider.get_live_price("RELIANCE.NS")
# hist = provider.get_historical_price("AAPL", "2023-01-01", "2023-01-31")
