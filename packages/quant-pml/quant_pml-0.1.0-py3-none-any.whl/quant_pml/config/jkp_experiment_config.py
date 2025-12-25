from __future__ import annotations

from dataclasses import dataclass

from quant_pml.config.us_experiment_config import (
    USExperimentConfig,
)


@dataclass
class JKPExperimentConfig(USExperimentConfig):
    def __init__(self) -> None:
        super().__init__()
        self.MCAP_SELECTION_QUANTILE = 0.8
        self.PREFIX = "jkp_"
