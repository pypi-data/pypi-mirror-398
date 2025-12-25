from __future__ import annotations

import pandas as pd

from quant_pml.config.topn_experiment_config import TopNExperimentConfig


class ResearchUSExperimentConfig(TopNExperimentConfig):
    def __init__(self) -> None:
        super().__init__(topn=3_000)

        self.HEDGE_FREQ = "D"
        self.DATA_PROCESSING_START_DATE = pd.Timestamp("2000-01-01")
        self.START_DATE = pd.Timestamp("2010-01-01")
        self.CAUSAL_WINDOW_END_DATE_FIELD = "end_date"
