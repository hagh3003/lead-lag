# lead-lag

Fetch one-minute OHLCV prices for one or more Yahoo Finance tickers:

```bash
python price_data.py AAPL MSFT --period 1d
```

The Python API returns a mapping from each normalized ticker to its timestamped
price rows:

```python
from price_data import pull_1_minute_prices

prices = pull_1_minute_prices(["AAPL", "MSFT"])
```