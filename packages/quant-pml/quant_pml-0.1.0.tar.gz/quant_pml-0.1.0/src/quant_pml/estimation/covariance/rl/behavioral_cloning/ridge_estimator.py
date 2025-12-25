from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

from quant_pml.cov_estimators.rl.base_rl_estimator import BaseRLCovEstimator


class RidgeCovEstimator(BaseRLCovEstimator):
    def __init__(self, shrinkage_type: str, window_size: int | None = None) -> None:
        super().__init__(shrinkage_type=shrinkage_type, window_size=window_size)

        self.last_pred = None
        self.encountered_nan = False

        self.scaler = StandardScaler()

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        # TODO(@V): Fix lagged target
        features = features.ffill()
        merged_df = features.merge(shrinkage_target, left_index=True, right_index=True)
        features = merged_df[features.columns]
        shrinkage_target = merged_df[merged_df.columns.difference(features.columns)]
        if shrinkage_target.isna().any().any():
            self.encountered_nan = True
        else:
            features = self.scaler.fit_transform(features)
            self.ridge = RidgeCV(
                alphas=np.logspace(-3, 3, 20),
                cv=TimeSeriesSplit(n_splits=5),
            )
            self.ridge.fit(X=features, y=shrinkage_target)
            self.encountered_nan = False

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        features = self.scaler.transform(features)
        if not self.encountered_nan:
            pred = self.ridge.predict(features).item()
            self.last_pred = pred
            return pred

        return self.last_pred
