from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies.optimization_data import TrainingData

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import TimeSeriesSplit

from quant_pml.estimation.covariance.rl.base_rl_estimator import BaseRLCovEstimator


class RidgePriorCovEstimator(BaseRLCovEstimator):
    def __init__(self, shrinkage_type: str, window_size: int | None = None) -> None:
        super().__init__(shrinkage_type=shrinkage_type, window_size=window_size)

        self.last_pred = None
        self.encountered_nan = False

        self.ridge = RidgeCV(
            alphas=np.logspace(-3, 3, 10),
            cv=TimeSeriesSplit(n_splits=5),
            fit_intercept=False,
        )

    def _normalize_target(self, target: pd.Series, data: TrainingData) -> pd.Series:
        ret = data.simple_excess_returns
        first_date = ret.index[-1] - pd.Timedelta(days=365)

        lw = LedoitWolf(store_precision=False)
        lw.fit(ret.loc[first_date:])
        lw_shrinkage = lw.shrinkage_

        return target - lw_shrinkage.item()

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        features = features.ffill()
        merged_df = features.merge(shrinkage_target, left_index=True, right_index=True)
        features = merged_df[features.columns]
        shrinkage_target = merged_df[merged_df.columns.difference(features.columns)].iloc[:, 0]
        if shrinkage_target.isna().any():
            self.encountered_nan = True
        else:
            self.ridge.fit(X=features, y=shrinkage_target)
            self.encountered_nan = False

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        if not self.encountered_nan:
            pred = self.ridge.predict(features).item()
            self.last_pred = pred
            return pred

        return self.last_pred
