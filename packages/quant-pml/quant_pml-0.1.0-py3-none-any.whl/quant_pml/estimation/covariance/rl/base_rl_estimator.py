from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from estimation.covariance.shrinkage.identity_based_cov_estimator import (
    IdentityBasedCovEstimator,
)
from sklearn.preprocessing import StandardScaler

from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator
from quant_pml.estimation.covariance.shrinkage.qis import QISCovEstimator

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData


class ShrinkageType(Enum):
    LINEAR = "linear"
    QIS = "qis"


class BaseRLCovEstimator(BaseCovEstimator):
    def __init__(
        self,
        shrinkage_type: str = "linear",
        window_size: int | None = None,
        *,
        refit: bool = True,
    ) -> None:
        super().__init__()

        self.shrinkage_type = ShrinkageType(shrinkage_type)
        self.window_size = window_size

        self.refit = refit
        self._trained = False

        self.feat_scaler = StandardScaler()

        if self.shrinkage_type == ShrinkageType.QIS:
            self.shrinkage = QISCovEstimator(
                shrinkage=1.0,  # Starting shrinkage, will be updated during fit
            )
        elif self.shrinkage_type == ShrinkageType.LINEAR:
            self.shrinkage = IdentityBasedCovEstimator(alphas=[0.1])
        else:
            msg = f"Unknown shrinkage type: {self.shrinkage_type}"
            raise NotImplementedError(msg)

        self._seen_training_data = None

        self._predictions = []
        self.trained_with_features = False

        self._seen_targets = None
        self._pred_lagged_tgt = None

    @abstractmethod
    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        raise NotImplementedError

    @abstractmethod
    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        raise NotImplementedError

    def _adjust_target_history(self, new_targets: pd.DataFrame) -> None:
        if self._seen_targets is None:
            self._seen_targets = new_targets
        else:
            new_dates = new_targets.index.difference(self._seen_targets.index)
            if len(new_dates) > 0:
                new_targets = new_targets.loc[new_dates]
                self._seen_targets = pd.concat([self._seen_targets, new_targets], axis=0)

    def _extract_features_targets(self, training_data: TrainingData) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        feat = training_data.macro_features

        if self.shrinkage_type == ShrinkageType.LINEAR:
            target = training_data.targets["target"]
            target_hist = self._seen_targets[["target"]].rename(columns={"target": "lagged_target"})
        elif self.shrinkage_type == ShrinkageType.QIS:
            target = training_data.targets["qis_shrinkage"]
            target_hist = self._seen_targets[["qis_shrinkage"]].rename(columns={"qis_shrinkage": "lagged_target"})
        else:
            msg = f"Unknown shrinkage type: {self.shrinkage_type}"
            raise NotImplementedError(msg)

        return feat, target, target_hist

    def _filter_estimation_window(self, features: pd.DataFrame, target: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
        start_date = target.index[-1] - pd.Timedelta(days=self.window_size) if self.window_size is not None else target.index[0]
        features = features.loc[start_date:]
        target = target.loc[start_date:]

        return features, target

    @staticmethod
    def _filter_valid_dates_range(features: pd.DataFrame, target: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
        first_feat_date = features.dropna(axis=0, how="any").first_valid_index() if features.shape[1] > 0 else features.index[0]
        last_feat_date = features.dropna(axis=0, how="any").last_valid_index() if features.shape[1] > 0 else features.index[-1]

        first_target_date = target.dropna(axis=0, how="any").first_valid_index()
        last_target_date = target.dropna(axis=0, how="any").last_valid_index()

        first_date = max(first_feat_date, first_target_date)
        last_date = min(last_feat_date, last_target_date)

        features = features.loc[first_date:last_date]
        target = target.loc[first_date:last_date]

        return features, target

    def _append_lagged_target(
        self, features: pd.DataFrame, target: pd.Series, target_history: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series]:
        add_features = target_history.copy()
        add_features["target_rolling_mean"] = add_features["lagged_target"].rolling(window=252, min_periods=1).mean()
        add_features["target_rolling_vol"] = add_features["lagged_target"].rolling(window=252, min_periods=1).std().fillna(0)
        self._pred_lagged_tgt = add_features.iloc[-1:, :]
        add_features = add_features.shift(1)

        features = pd.merge_asof(
            features,
            add_features,
            tolerance=pd.Timedelta("1D"),
            left_index=True,
            right_index=True,
        )
        first_feat_date = features.dropna(axis=0, how="any").first_valid_index()
        first_target_date = target.dropna(axis=0, how="any").first_valid_index()

        first_lagged_date = max(first_feat_date, first_target_date)

        features = features.loc[first_lagged_date:]
        target = target.loc[first_lagged_date:]

        return features, target

    def _fit(self, training_data: TrainingData) -> None:
        self._seen_training_data = training_data

        if self._trained and not self.refit:
            return

        self._adjust_target_history(training_data.targets)

        feat, target, target_hist = self._extract_features_targets(training_data)

        feat, target = self._filter_estimation_window(feat, target)
        feat, target = self._filter_valid_dates_range(feat, target)

        target = self._normalize_target(target, data=training_data)

        feat, target = self._append_lagged_target(feat, target, target_hist)

        feat_transf = self.feat_scaler.fit_transform(feat)
        feat = pd.DataFrame(feat_transf, index=feat.index, columns=feat.columns)

        self.shrinkage.available_assets = self.available_assets
        self._fit_shrinkage(features=feat, shrinkage_target=target)

    def _normalize_target(self, target: pd.Series, data: TrainingData) -> pd.Series:
        return target

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:
        feat = prediction_data.macro_features
        feat[self._pred_lagged_tgt.columns] = self._pred_lagged_tgt.to_numpy()

        feat_transformed = self.feat_scaler.transform(feat)
        feat = pd.DataFrame(feat_transformed, index=feat.index, columns=feat.columns)

        pred_shrinkage = self._predict_shrinkage(feat)

        if self.shrinkage_type == ShrinkageType.LINEAR:
            pred_shrinkage = np.clip(pred_shrinkage, 0, 1)
            self.shrinkage.alphas = [pred_shrinkage]
        elif self.shrinkage_type == ShrinkageType.QIS:
            self.shrinkage.shrinkage = pred_shrinkage
        else:
            msg = f"Unknown shrinkage type: {self.shrinkage_type}"
            raise NotImplementedError(msg)

        self._predictions.append([feat.index[-1], pred_shrinkage])

        self.shrinkage.fit(training_data=self._seen_training_data)

        self._seen_training_data = None

        return self.shrinkage.predict(prediction_data=prediction_data)

    @property
    def predictions(self) -> pd.DataFrame:
        pred = pd.DataFrame(self._predictions, columns=["date", "prediction"])
        pred["date"] = pd.to_datetime(pred["date"])
        return pred.set_index("date")
