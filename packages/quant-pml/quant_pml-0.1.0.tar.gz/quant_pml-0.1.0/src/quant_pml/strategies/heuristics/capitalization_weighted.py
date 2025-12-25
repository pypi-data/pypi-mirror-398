from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

from quant_pml.strategies.base_strategy import BaseStrategy
from quant_pml.strategies.weighting.weighting_mixin import WeightingMixin


class CapWeightedStrategy(BaseStrategy, WeightingMixin):
    def __init__(self) -> None:
        BaseStrategy.__init__(self)
        WeightingMixin.__init__(self, weighting_scheme="cap_weighted")

    def _fit(self, training_data: TrainingData) -> None:
        pass

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        w = self.set_weights(
            data=prediction_data,
            weights_=weights_,
            long_upper=self.available_assets,
            short_lower=[],
        )
        return w
