from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import numpy as np

from quant_pml.strategies.factors.enhanced.fractional_momentum import FractionalMomentum
from quant_pml.strategies.factors.sorting_strategy import FactorMode


class FractionalMomentumSampleMean(FractionalMomentum):
    Z_SCORE = 0

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

    def get_scores(self, data: TrainingData) -> pd.Series:
        prices = data.prices.loc[:, self.available_assets]

        fm_mu_pred = self._calculate_fractional_momentum(
            prices=np.log(prices),
        )
        fm_mu_pred = fm_mu_pred.dropna()

        vols = data.log_excess_returns.loc[:, fm_mu_pred.index].std(axis=0)

        return fm_mu_pred / vols

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:  # noqa: ARG002
        scores = self.get_scores(data=self._seen_data)

        if self.mode == FactorMode.LONG:
            long_upper = scores[scores >= self.Z_SCORE].index.tolist()
            short_lower = []
        elif self.mode == FactorMode.SHORT:
            long_upper = []
            short_lower = scores[scores <= -self.Z_SCORE].index.tolist()
        else:
            long_upper = scores[scores >= self.Z_SCORE].index.tolist()
            short_lower = scores[scores <= -self.Z_SCORE].index.tolist()

        return self.set_weights(
            data=self._seen_data,
            weights_=weights_,
            long_upper=long_upper,
            short_lower=short_lower,
        )
