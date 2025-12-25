from __future__ import annotations

from abc import ABC

from quant_pml.estimation.base_estimator import BaseEstimator


class BaseMuEstimator(BaseEstimator, ABC):
    def __init__(self) -> None:
        super().__init__()
