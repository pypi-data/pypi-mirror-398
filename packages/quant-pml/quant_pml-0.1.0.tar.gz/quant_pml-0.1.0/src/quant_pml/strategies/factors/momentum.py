from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import TrainingData

import numpy as np
import pandas as pd

from quant_pml.strategies.factors.sorting_strategy import SortingStrategy


class Momentum(SortingStrategy):
    def __init__(  # noqa: PLR0913
        self,
        mode: str,
        sign: int = 1,
        *,
        as_zscore: bool = False,
        window_days: int = 365,
        exclude_last_days: int = 30,
        quantile: float | None = None,
        n_holdings: int | None = None,
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        super().__init__(
            quantile=quantile,
            mode=mode,
            n_holdings=n_holdings,
            weighting_scheme=weighting_scheme,
        )
        self.sign = sign
        self.as_zscore = as_zscore
        self.window_days = window_days
        self.exclude_last_days = exclude_last_days

    def get_scores(self, data: TrainingData) -> pd.Series:
        targets = data.simple_total_returns

        first_date = targets.index[-1] - pd.Timedelta(days=self.window_days)
        last_date = targets.index[-1] - pd.Timedelta(days=self.exclude_last_days)

        use_returns = targets.loc[first_date:last_date]

        cumm_r = use_returns.add(1).prod(axis=0) - 1
        if self.as_zscore:
            cumm_r = cumm_r.div(use_returns.std(axis=0) * np.sqrt(self.window_days - self.exclude_last_days))

        return self.sign * cumm_r
