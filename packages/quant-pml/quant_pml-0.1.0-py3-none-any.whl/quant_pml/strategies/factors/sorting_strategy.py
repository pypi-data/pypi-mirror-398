from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd

from quant_pml.strategies.base_strategy import BaseStrategy
from quant_pml.strategies.weighting.weighting_mixin import WeightingMixin


class FactorMode(Enum):
    LONG = "long"
    SHORT = "short"
    LONG_SHORT = "long_short"


class SortingStrategy(BaseStrategy, WeightingMixin, ABC):
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

        self._seen_data = None

        self._sorting = {}
        self._scores = pd.DataFrame()

    @abstractmethod
    def get_scores(self, data: TrainingData) -> pd.Series:
        raise NotImplementedError

    def _fit(self, training_data: TrainingData) -> None:
        self._seen_data = training_data

    def _get_sorting_weights(self, data: TrainingData, weights_: pd.DataFrame) -> tuple[pd.DataFrame, pd.Index, pd.Index]:
        scores = self.get_scores(data=data).dropna()
        self._save_scores(pred_date=data.pred_date, scores=scores)
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

        weights_ = self.set_weights(
            data=data,
            weights_=weights_,
            long_upper=long_upper,
            short_lower=short_lower,
        )

        return weights_, long_upper, short_lower

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        weights_, _, _ = self._get_sorting_weights(data=self._seen_data, weights_=weights_)
        return weights_

    def _save_scores(self, pred_date: pd.Timestamp, scores: pd.Series) -> None:
        self._scores.loc[pred_date, scores.index] = scores.to_numpy()

    @property
    def scores(self) -> pd.DataFrame:
        return self._scores
