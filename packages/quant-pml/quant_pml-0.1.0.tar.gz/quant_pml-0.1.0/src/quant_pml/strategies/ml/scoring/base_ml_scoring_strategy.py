from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData

from abc import ABC, abstractmethod

from quant_pml.strategies.base_strategy import BaseStrategy
from quant_pml.strategies.factors.sorting_strategy import FactorMode
from quant_pml.strategies.weighting.weighting_mixin import WeightingMixin


class BaseMLScoringStrategy(BaseStrategy, WeightingMixin, ABC):
    def __init__(
        self,
        mode: str,
        quantile: float | None = None,
        n_holdings: int | None = None,
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        BaseStrategy.__init__(self)
        WeightingMixin.__init__(self, weighting_scheme=weighting_scheme)
        ABC.__init__(self)

        if quantile is None and n_holdings is None:
            msg = "Either `quantile` or `n_holdings` must be specified."
            raise ValueError(msg)

        self.quantile = quantile
        self.n_holdings = n_holdings
        self.mode = FactorMode(mode)

    @abstractmethod
    def predict_scores(self, prediction_data: PredictionData) -> pd.Series:
        raise NotImplementedError

    def _get_sorting_weights(self, scores: pd.Series, data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        scores_sorted = scores.sort_values(ascending=False)
        sorted_assets = scores_sorted.index.tolist()

        n_quantile = max(int(len(sorted_assets) * self.quantile), 1) if self.n_holdings is None else self.n_holdings

        if self.mode == FactorMode.LONG:
            long_upper = sorted_assets[:n_quantile]
            short_lower = []
        elif self.mode == FactorMode.SHORT:
            long_upper = []
            short_lower = sorted_assets[-n_quantile:]
        else:
            long_upper = sorted_assets[:n_quantile]
            short_lower = sorted_assets[-n_quantile:]

        return self.set_weights(
            data=data,
            weights_=weights_,
            long_upper=long_upper,
            short_lower=short_lower,
        )

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        scores = self.predict_scores(prediction_data=prediction_data)
        return self._get_sorting_weights(scores=scores, data=prediction_data, weights_=weights_)
