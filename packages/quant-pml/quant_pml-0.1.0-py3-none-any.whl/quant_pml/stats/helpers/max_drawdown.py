from __future__ import annotations

import pandas as pd


def max_drawdown(prices: pd.Series[float]) -> pd.Series[float]:
    max_drawdown_series = pd.Series(index=prices.index)
    for time, price in prices.items():
        lowest_price = prices[time:].min()  # type: ignore[misc]
        max_drawdown_series[time] = (price - lowest_price) / price
    return max_drawdown_series
