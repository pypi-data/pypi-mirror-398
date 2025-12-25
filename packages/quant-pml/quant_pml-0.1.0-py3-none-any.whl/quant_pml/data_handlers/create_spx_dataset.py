from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.config.base_experiment_config import BaseExperimentConfig

from pathlib import Path

from quant_pml.data_handlers.create_crsp_dataset import create_crsp_dataset
from quant_pml.data_handlers.universe_builder_functions import (
    load_precomputed_builder_fn,
)


def create_spx_dataset(
    cfg: BaseExperimentConfig,
    filename: str = "spx_presence_matrix.csv",
    path: Path = Path("../../../data/precomputed_pms"),
) -> None:
    universe_builder_fns = [
        lambda data: load_precomputed_builder_fn(data, filename=filename, path=path),
    ]

    create_crsp_dataset(
        config=cfg,
        universe_builder_fns=universe_builder_fns,
    )


if __name__ == "__main__":
    from quant_pml.config.spx_experiment_config import SPXExperimentConfig

    settings = SPXExperimentConfig()
    create_spx_dataset(settings)
