from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData, TrainingData


from quant_pml.strategies.base_strategy import BaseStrategy


class TargetStrategy(BaseStrategy):
    def __init__(self, target_weights: pd.Series) -> None:
        super().__init__()
        self.target_weights = target_weights
        self.all_assets = target_weights.index.tolist()
        self.available_assets = target_weights.index.tolist()

    def _fit(self, training_data: TrainingData) -> None:
        pass

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:  # noqa: ARG002
        weights_.loc[:, self.target_weights.index] = self.target_weights.to_numpy()
        return weights_
