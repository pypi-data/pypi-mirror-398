from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from pmplib.strategies.optimization_data import PredictionData, TrainingData

from pmplib.features.ols_betas import get_window_betas
from pmplib.strategies.factors.sorting_strategy import SortingStrategy


class LowBeta(SortingStrategy):
    def __init__(  # noqa: PLR0913
        self,
        mode: str,
        mkt_name: str,
        quantile: float | None = None,
        n_holdings: int | None = None,
        window_days: int | None = 365,
        *,
        mkt_neutral: bool = True,
        drop_negative_betas: bool = True,
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        super().__init__(
            quantile=quantile,
            mode=mode,
            n_holdings=n_holdings,
            weighting_scheme=weighting_scheme,
        )

        self.mkt_name = mkt_name
        self.window_days = window_days
        self.mkt_neutral = mkt_neutral
        self.drop_negative_betas = drop_negative_betas

        self._betas = None

    def get_scores(self, data: TrainingData) -> pd.Series:
        betas = get_window_betas(
            market_index=data.factors[self.mkt_name],
            targets=data.simple_excess_returns,
            window_days=self.window_days,
        )
        self._betas = betas[betas > 0] if self.drop_negative_betas else betas

        return -self._betas

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        weights_, long_upper, short_lower = self._get_sorting_weights(
            data=self._seen_data,
            weights_=weights_,
        )

        if self.mkt_neutral:
            beta_low = self._betas.loc[long_upper].mean()
            beta_high = self._betas.loc[short_lower].mean()

            weights_.loc[:, long_upper] = weights_.loc[:, long_upper] / beta_low
            weights_.loc[:, short_lower] = weights_.loc[:, short_lower] / beta_high

        return weights_
