from __future__ import annotations

from dataclasses import dataclass

from quant_pml.config.us_experiment_config import (
    USExperimentConfig,
)


@dataclass
class SPXExperimentConfig(USExperimentConfig):
    def __init__(self) -> None:
        super().__init__()

        self.PREFIX = "spx_"
