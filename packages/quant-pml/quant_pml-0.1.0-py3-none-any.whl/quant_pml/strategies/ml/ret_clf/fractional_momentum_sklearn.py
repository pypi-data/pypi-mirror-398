from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData

import numpy as np
from sklearn.linear_model import LogisticRegression

from quant_pml.strategies.factors.enhanced.fractional_momentum import FractionalMomentum
from quant_pml.strategies.factors.sorting_strategy import FactorMode


class FractionalMomentumSklearn(FractionalMomentum):
    def __init__(  # noqa: PLR0913
        self,
        threshold: float,
        d: float,
        window_size: int,
        mode: str,
        quantile: float | None = None,
        n_holdings: int | None = None,
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        super().__init__(
            quantile=quantile,
            n_holdings=n_holdings,
            mode=mode,
            weighting_scheme=weighting_scheme,
            threshold=threshold,
            d=d,
            window_size=window_size,
        )

        self.logreg = LogisticRegression(random_state=3)

    def _estimate_mu_hat(self, p_fd_df: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
        x = p_fd_df.shift(1).dropna(axis=0)
        x = x / x.mean(axis=0)

        y = prices.pct_change().dropna(axis=0) >= 0  # noqa: F841

        raise NotImplementedError

    def get_scores(self, data: PredictionData) -> pd.Series:
        prices = data.prices.loc[:, self.available_assets]

        return self._calculate_fractional_momentum(
            prices=np.log(prices),
        )

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:  # noqa: ARG002
        scores = self.get_scores(data=self._seen_data)
        scores = scores[scores.notna()]

        if self.mode == FactorMode.LONG:
            long_upper = scores[scores > 0].index.tolist()
            short_lower = []
        elif self.mode == FactorMode.SHORT:
            long_upper = []
            short_lower = scores[scores < 0].index.tolist()
        else:
            long_upper = scores[scores > 0].index.tolist()
            short_lower = scores[scores < 0].index.tolist()

        return self.set_weights(
            data=self._seen_data,
            weights_=weights_,
            long_upper=long_upper,
            short_lower=short_lower,
        )
