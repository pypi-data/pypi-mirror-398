from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_pml.config.us_experiment_config import (
    USExperimentConfig,
)


@dataclass
class TopNExperimentConfig(USExperimentConfig):
    def __init__(self, topn: int = 20) -> None:
        super().__init__()

        self.TOPN = topn
        self.PREFIX = f"top{self.TOPN}_"

        self.PATH_TARGETS = Path(__file__).resolve().parents[2] / "data" / "targets"
