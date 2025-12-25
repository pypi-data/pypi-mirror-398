from __future__ import annotations

import numpy as np
import pandas as pd

from quant_pml.base.returns import Returns


class Prices:
    def __init__(self, prices: pd.DataFrame) -> None:
        self._prices = prices

    def to_returns(self) -> Returns:
        return Returns().from_prices(self._prices)

    def from_simple_returns(self, simple_returns: pd.DataFrame) -> Prices:
        prices = simple_returns.add(1).cumprod()
        self._prices = pd.DataFrame(prices, index=simple_returns.index, columns=simple_returns.columns)
        return Prices(self._prices)

    def from_log_returns(self, simple_returns: pd.DataFrame) -> Prices:
        prices = np.exp(simple_returns.to_numpy().cumsum())
        self._prices = pd.DataFrame(prices, index=simple_returns.index, columns=simple_returns.columns)
        return Prices(self._prices)

    def truncate(self, n_periods: int) -> Prices:
        return Prices(self._prices.iloc[n_periods:])  # type: ignore  # noqa: PGH003

    @property
    def df(self) -> pd.DataFrame:
        return self._prices
