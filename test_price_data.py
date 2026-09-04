import json
import unittest
from unittest.mock import patch

from price_data import fetch_one_minute_prices, pull_1_minute_prices


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps(self.payload).encode()


def payload(close):
    return {
        "chart": {
            "result": [
                {
                    "timestamp": [1704067200],
                    "indicators": {"quote": [{"open": [close - 1], "high": [close], "low": [close - 2], "close": [close], "volume": [10]}]},
                }
            ]
        }
    }


class PriceDataTests(unittest.TestCase):
    def test_fetches_one_minute_rows_and_encodes_ticker(self):
        calls = []

        def opener(url, timeout):
            calls.append((url, timeout))
            return Response(payload(101))

        rows = fetch_one_minute_prices(" msft ", opener=opener)

        self.assertEqual(rows[0]["close"], 101)
        self.assertIn("MSFT", calls[0][0])
        self.assertIn("interval=1m", calls[0][0])

    @patch("price_data.fetch_one_minute_prices")
    def test_pulls_all_unique_tickers(self, fetch):
        fetch.side_effect = lambda ticker, period="1d": [{"ticker": ticker, "period": period}]

        self.assertEqual(
            pull_1_minute_prices(["aapl", "MSFT", "aapl"]),
            {
                "AAPL": [{"ticker": "AAPL", "period": "1d"}],
                "MSFT": [{"ticker": "MSFT", "period": "1d"}],
            },
        )

    def test_rejects_empty_ticker(self):
        with self.assertRaises(ValueError):
            fetch_one_minute_prices(" ")


if __name__ == "__main__":
    unittest.main()
