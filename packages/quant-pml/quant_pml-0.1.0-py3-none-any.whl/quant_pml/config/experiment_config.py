from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class BaseExperimentConfig:
    RANDOM_SEED: int = field(default=12, metadata={"docs": "Fix random seed"})

    # Folders
    PATH_OUTPUT: Path = field(
        default=Path(__file__).resolve().parents[2] / "data" / "output",
        metadata={"docs": "Relative path to data folder"},
    )

    SAVE_PATH: Path = field(
        default=Path(__file__).resolve().parents[2] / "data" / "run",
        metadata={"docs": "Relative path to data folder"},
    )

    # Filename
    DF_FILENAME: str = field(default="data_df.csv", metadata={"docs": "Preprocessed data"})

    # Experiment Settings
    TRAIN_START_DATE: pd.Timestamp = field(
        default=pd.to_datetime("1980-01-01"),
        metadata={"docs": "Date to start training"},
    )

    TRAIN_END_DATE: pd.Timestamp = field(
        default=pd.to_datetime("2024-01-01"),
        metadata={"docs": "Date to end train"},
    )

    TEST_END_DATE: pd.Timestamp = field(
        default=pd.to_datetime("2024-12-15"),
        metadata={"docs": "Date to end analysis"},
    )

    REBALANCE_FREQ_DAYS: int = field(
        default=5 * 4,
        metadata={"docs": "Frequency of rebalancing"},
    )

    HEDGE_FREQ_DAYS: int = field(
        default=1,
        metadata={"docs": "Frequency of hedging"},
    )

    LAG_DAYS: int = field(
        default=1,
        metadata={"docs": "Number of days to lag for feature observation"},
    )

    N_LOOKBEHIND_PERIODS: int = field(
        default=1 * 30,
        metadata={"docs": "Number of rebalance periods to take into rolling regression"},
    )

    MIN_ROLLING_PERIODS: int = field(
        default=12,
        metadata={"docs": "Number of minimum rebalance periods to run the strategy"},
    )

    # Universe Setting
    ASSET_UNIVERSE: tuple[str] = field(
        default=("MOEX_INDEX",),
        metadata={"docs": "Tradeable assets tuple"},
    )

    FACTORS: tuple[str] = field(
        default=("MOEX_INDEX",),
        metadata={"docs": "Tradeable factors tuple"},
    )

    HEDGING_ASSETS: tuple[str] = field(
        default=("spx_fut",),
        metadata={"docs": "Tradeable assets tuple"},
    )

    RF_NAME: str = field(
        default="acc_rate",
        metadata={"docs": "Risk-Free rate column name"},
    )

    def __str__(self) -> str:
        string = f"{self.__class__.__name__}:"
        for key, value in self.__dict__.items():
            string += f"\n* {key} = {value}"
        return string

    def __repr__(self) -> str:
        return self.__str__()
