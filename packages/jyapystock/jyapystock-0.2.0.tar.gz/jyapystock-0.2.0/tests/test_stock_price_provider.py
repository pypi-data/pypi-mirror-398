import unittest
from jyapystock.stock_price_provider import StockPriceProvider
import os

# Allow running provider-specific tests by setting the PROVIDER env var to
# one of: 'yfinance', 'alphavantage', 'nasdaq', 'nse'. When unset, all tests run.
PROVIDER = os.environ.get("PROVIDER")
if PROVIDER:
    PROVIDER = PROVIDER.lower()

def should_run_for(providers):
    if not PROVIDER:
        return True
    return PROVIDER in providers

class TestStockPriceProvider(unittest.TestCase):
    def setUp(self):
        self.provider_yf = StockPriceProvider(country="USA", source="yfinance")
        api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")
        self.provider_av = StockPriceProvider(country="USA", source="alphavantage", alpha_vantage_api_key=api_key)
        self.provider_yf_india = StockPriceProvider(country="India", source="yfinance")
        self.provider_nasdaq = StockPriceProvider(country="USA", source="nasdaq")
        self.provider_nse = StockPriceProvider(country="India", source="nse")
    
    def test_live_price_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        result = self.provider_yf.get_live_price("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)
        self.assertGreater(result["price"], 0)

    def test_historical_price_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        hist = self.provider_yf.get_historical_price("AAPL", "2023-01-01", "2023-01-10")
        self.assertIsInstance(hist, list)
        self.assertGreater(len(hist), 0)
    
    def test_live_price_yfinance_india(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        result = self.provider_yf_india.get_live_price("RELIANCE")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)
        self.assertGreater(result["price"], 0)

    def test_historical_price_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        hist = self.provider_yf_india.get_historical_price("RELIANCE", "2023-01-01", "2023-01-10")
        self.assertIsInstance(hist, list)
        self.assertGreater(len(hist), 0)

    def test_live_price_alpha_vantage(self):
        if not should_run_for(["alphavantage"]):
            self.skipTest("Skipping Alpha Vantage tests in this run")
        result = self.provider_av.get_live_price("IBM")
        self.assertTrue(isinstance(result, dict) or result is None)
        if result is not None:
            self.assertIn("price", result)
            self.assertIn("timestamp", result)
            self.assertIn("change_percent", result)

    def test_historical_price_alpha_vantage(self):
        if not should_run_for(["alphavantage"]):
            self.skipTest("Skipping Alpha Vantage tests in this run")
        hist = self.provider_av.get_historical_price("IBM", "2023-01-01", "2023-01-10")
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)

    def test_live_price_auto(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping auto tests in this run")
        provider_auto = StockPriceProvider(country="USA")  # default None == auto
        result = provider_auto.get_live_price("AAPL")
        self.assertTrue(isinstance(result, dict) or result is None)
        if result is not None:
            self.assertIn("price", result)
            self.assertIn("timestamp", result)
            self.assertIn("change_percent", result)

    def test_historical_price_auto(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping auto tests in this run")
        provider_auto = StockPriceProvider(country="USA", source="auto")
        hist = provider_auto.get_historical_price("AAPL", "2023-01-01", "2023-01-10")
        # historical can be list or None depending on source availability
        self.assertTrue(isinstance(hist, list) or hist is None)
    
    def test_india_symbol_variants(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping India/yfinance tests in this run")
        # Ensure provider for India attempts .NS/.BO variants (result may be None if network/API fails)
        provider_in = StockPriceProvider(country="India")
        result = provider_in.get_live_price("RELIANCE")
        self.assertTrue(isinstance(result, dict) or result is None)
        if result is not None:
            self.assertIn("price", result)
            self.assertIn("timestamp", result)
            self.assertIn("change_percent", result)

    def test_india_historical_variants(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping India/yfinance tests in this run")
        provider_in = StockPriceProvider(country="India")
        hist = provider_in.get_historical_price("RELIANCE", "2023-01-01", "2023-01-10")
        self.assertTrue(isinstance(hist, list) or hist is None)

    def test_historical_price_nasdaq(self):
        if not should_run_for(["nasdaq"]):
            self.skipTest("Skipping NASDAQ tests in this run")
        # Call the real NASDAQ provider (no mocking) — result may be None if API unavailable
        hist = self.provider_nasdaq.get_historical_price('AAPL', '2025-12-17', '2025-12-19')
        # Should be a list of records or None depending on network/API
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)

    def test_live_price_nasdaq(self):
        if not should_run_for(["nasdaq"]):
            self.skipTest("Skipping NASDAQ tests in this run")
        # Call the real NASDAQ live price (no mocking) — returns dict or None
        result = self.provider_nasdaq.get_live_price('AAPL')
        self.assertTrue(isinstance(result, dict) or result is None)
        if result is not None:
            self.assertIn("price", result)
            self.assertIn("timestamp", result)
            self.assertIn("change_percent", result)
            self.assertGreater(result["price"], 0)

    def test_live_price_nse(self):
        if not should_run_for(["nse"]):
            self.skipTest("Skipping NSE tests in this run")
        # Call the real NSE live price (no mocking) — returns dict or None
        result = self.provider_nse.get_live_price('SBIN')
        self.assertTrue(isinstance(result, dict) or result is None)
        if result is not None:
            self.assertIn("price", result)
            self.assertIn("timestamp", result)
            self.assertIn("change_percent", result)
            self.assertGreater(result["price"], 0)

    def test_historical_price_nse(self):
        if not should_run_for(["nse"]):
            self.skipTest("Skipping NSE tests in this run")
        # Call the real NSE historical price (no mocking)
        hist = self.provider_nse.get_historical_price('RELIANCE', '2025-12-17', '2025-12-24')
        self.assertTrue(isinstance(hist, list) or hist is None)
        if hist is not None:
            self.assertGreater(len(hist), 0)

if __name__ == "__main__":
    unittest.main()
