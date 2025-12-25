from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

import numpy as np


def simple_to_log_returns(simple_returns: pd.DataFrame) -> pd.DataFrame:
    return np.log(1 + simple_returns)  # type: ignore  # noqa: PGH003


def log_to_simple_returns(log_returns: pd.DataFrame) -> pd.DataFrame:
    return np.exp(log_returns) - 1  # type: ignore  # noqa: PGH003


class Returns:
    def __init__(
        self,
        simple_returns: pd.DataFrame | None = None,
        log_returns: pd.DataFrame | None = None,
    ) -> None:
        self.simple_returns = simple_returns
        self.log_returns = log_returns

        if simple_returns is not None:
            self.log_returns = simple_to_log_returns(simple_returns)
        elif log_returns is not None:
            self.simple_returns = log_to_simple_returns(log_returns)

    @staticmethod
    def from_prices(prices: pd.DataFrame) -> Returns:
        simple_returns = prices.ffill().pct_change(fill_method=None).iloc[1:]
        log_returns = simple_to_log_returns(simple_returns)
        return Returns(simple_returns=simple_returns, log_returns=log_returns)

    def truncate(self, n_periods: int) -> Returns:
        return Returns(self.simple_returns.iloc[n_periods:], self.log_returns.iloc[n_periods:])  # type: ignore  # noqa: PGH003
