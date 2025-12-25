from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from pmplib.strategies.optimization_data import TrainingData

from pmplib.strategies.factors.low_beta import LowBeta


class HighBeta(LowBeta):
    def __init__(  # noqa: PLR0913
        self,
        mode: str,
        mkt_name: str,
        quantile: float | None = None,
        n_holdings: int | None = None,
        mkt_neutral: bool = True,  # noqa: FBT002, FBT001
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        super().__init__(
            quantile=quantile,
            mode=mode,
            n_holdings=n_holdings,
            mkt_name=mkt_name,
            mkt_neutral=mkt_neutral,
            weighting_scheme=weighting_scheme,
        )

    def get_scores(self, data: TrainingData) -> pd.Series:
        return -self.get_scores(data=data)
