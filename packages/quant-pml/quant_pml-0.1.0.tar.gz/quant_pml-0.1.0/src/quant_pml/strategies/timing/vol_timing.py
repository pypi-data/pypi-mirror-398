from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import pandas as pd
from pandas.tseries.offsets import BusinessDay, MonthEnd, Week

from quant_pml.strategies.base_strategy import BaseStrategy


class VolTiming(BaseStrategy):
    def __init__(self, lookback: int | str, max_exposure: float) -> None:
        super().__init__()

        if isinstance(lookback, str):
            if lookback in ("ME", "MS"):
                self.lookback = MonthEnd(n=1)
            elif lookback in ("WE", "WS"):
                self.lookback = Week(n=1)
            else:
                self.lookback = BusinessDay(n=1)
        elif isinstance(lookback, int):
            self.lookback = lookback
        else:
            msg = f"`lookback` must be an integer or pandas frequency, got {type(lookback)}."
            raise TypeError(msg)

        self.max_exposure = max_exposure

        self.trailing_variances = {}
        self.current_variances = None

        self._predicts = []

    def _fit(self, training_data: TrainingData) -> None:
        use_targets = training_data.simple_excess_returns
        if isinstance(self.lookback, int):
            first_date = use_targets.index[-1] - pd.Timedelta(days=self.lookback)
        else:
            first_date = use_targets.index[-1] - self.lookback

        self.current_variances = use_targets.loc[first_date:].var(axis=0) * 252

        for asset in self.current_variances.index:
            if asset not in self.trailing_variances:
                self.trailing_variances[asset] = []
            self.trailing_variances[asset].append(self.current_variances[asset])

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        trailing_vars = pd.DataFrame(self.trailing_variances)
        trailing_vars = trailing_vars.mean(axis=0)

        weights = trailing_vars / self.current_variances
        self._predicts.append([prediction_data.macro_features.index[-1], *(weights >= 1).tolist()])
        weights = weights.clip(lower=0, upper=self.max_exposure)

        weights_.loc[:, self.available_assets] = weights.to_numpy()

        return weights_

    @property
    def predicts(self) -> pd.DataFrame:
        return pd.DataFrame(self._predicts, columns=["date", *self.available_assets]).set_index("date")
