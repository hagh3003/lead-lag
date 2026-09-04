"""Retrieve one-minute price data for a collection of tickers."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable, Iterable
from urllib.parse import quote
from urllib.request import urlopen

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"


class PriceFetchError(RuntimeError):
    """Raised when a ticker's price data cannot be retrieved."""


def _decode_chart(ticker: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        result = payload["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote_data = result["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise PriceFetchError(f"Invalid price response for {ticker}") from exc

    prices = []
    fields = ("open", "high", "low", "close", "volume")
    for index, timestamp in enumerate(timestamps):
        row = {"timestamp": datetime.fromtimestamp(timestamp, timezone.utc).isoformat()}
        for field in fields:
            values = quote_data.get(field, [])
            row[field] = values[index] if index < len(values) else None
        prices.append(row)
    return prices


def fetch_one_minute_prices(
    ticker: str,
    period: str = "1d",
    timeout: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> list[dict[str, Any]]:
    """Fetch one-minute OHLCV rows for one ticker from Yahoo Finance."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must not be empty")
    url = f"{_CHART_URL.format(ticker=quote(ticker, safe=''))}?interval=1m&period1=0"
    url += f"&range={quote(period, safe='')}"
    try:
        with opener(url, timeout=timeout) as response:
            payload = json.load(response)
    except Exception as exc:
        raise PriceFetchError(f"Unable to fetch prices for {ticker}") from exc
    return _decode_chart(ticker, payload)


def pull_1_minute_prices(
    tickers: Iterable[str],
    period: str = "1d",
    max_workers: int = 8,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch one-minute prices for every ticker, concurrently."""
    normalized = list(dict.fromkeys(ticker.strip().upper() for ticker in tickers))
    if any(not ticker for ticker in normalized):
        raise ValueError("tickers must not contain empty values")
    if not normalized:
        return {}
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    workers = min(max_workers, len(normalized))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        rows = executor.map(lambda ticker: fetch_one_minute_prices(ticker, period), normalized)
        return dict(zip(normalized, rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to fetch")
    parser.add_argument("--period", default="1d", help="Yahoo Finance range (default: 1d)")
    args = parser.parse_args()
    print(json.dumps(pull_1_minute_prices(args.tickers, args.period)))


if __name__ == "__main__":
    main()
