from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pmplib.strategies.optimization_data import PredictionData

from pmplib.strategies.factors.momentum import Momentum
from pmplib.strategies.factors.sorting_strategy import FactorMode

if TYPE_CHECKING:
    import pandas as pd


class MomentumSign(Momentum):
    def __init__(  # noqa: PLR0913
        self,
        mode: str,
        *,
        as_zscore: bool = True,
        window_days: int = 365,
        exclude_last_days: int = 30,
        quantile: float | None = None,
        n_holdings: int | None = None,
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        super().__init__(
            quantile=quantile,
            n_holdings=n_holdings,
            mode=mode,
            as_zscore=as_zscore,
            window_days=window_days,
            exclude_last_days=exclude_last_days,
            weighting_scheme=weighting_scheme,
        )

    def get_scores(self, prediction_data: PredictionData) -> pd.Series:
        cumm_r = self.get_scores(prediction_data=prediction_data)

        if self.mode == FactorMode.LONG:
            cumm_r = cumm_r[cumm_r > 0]

        if self.mode == FactorMode.SHORT:
            cumm_r = cumm_r[cumm_r < 0]

        return cumm_r
