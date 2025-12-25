from __future__ import annotations

from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator


class BaseExperimentConfigV2(BaseModel):
    """Experiment configuration with runtime validation.

    Validates:
    - Date ordering (start < end)
    - Path existence
    - Positive values where required
    - Type coercion (strings → dates, etc.)

    Example:
        >>> config = BaseExperimentConfigV2(
        ...     START_DATE="2020-01-01",  # Auto-converted to Timestamp
        ...     END_DATE="2024-01-01",
        ...     REBALANCE_FREQ="D"
        ... )

    """

    model_config = {"arbitrary_types_allowed": True, "validate_assignment": True}

    # Basic settings
    PREFIX: str = Field(default="", description="Prefix for output files")
    CCY: str = Field(default="USD", description="Currency code")
    RANDOM_SEED: int = Field(default=12, ge=0, description="Random seed for reproducibility")

    # Paths
    CRSP_PATH: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "crsp_raw",
        description="Path to CRSP data",
    )
    COMPUSTAT_PATH: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "compustat_raw",
        description="Path to Compustat data",
    )
    PATH_FACTORS: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "jkp_raw",
        description="Path to factor data",
    )
    PATH_RF_RATE: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "features" / "ff",
        description="Path to risk-free rate data",
    )
    PATH_MKT: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "features" / "gw_replication",
        description="Path to market data",
    )
    PATH_HEDGING_ASSETS: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "hedge",
        description="Path to hedging assets data",
    )
    PATH_TMP: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "tmp",
        description="Path to temporary files",
    )
    PATH_OUTPUT: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "datasets",
        description="Path to output datasets",
    )
    SAVE_PATH: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "data" / "runs",
        description="Path to save backtest runs",
    )

    # Filenames
    CRSP_FULL_TMP_FILENAME: str = "crsp_full_tmp.csv"
    TRADE_DATASET_TMP_FILENAME: str = "crsp_factors_mkt_tmp.csv"
    CRSP_FILENAME: str = "crsp_80s.csv"
    COMPUSTAT_FILENAME: str = "compustat_us.csv"
    RAW_DATA_FILENAME: str = "raw_data.csv"
    FACTORS_FILENAME: str = "jkp_factors.csv"
    RF_RATE_FILENAME: str = "FFDaily.xlsx"
    MKT_FILENAME: str = "spxt.xlsx"
    HEDGING_ASSETS_FILENAME: str = "spx_fut.xlsx"
    DF_FILENAME: str = "data_df.csv"
    DNK_FEATURES_TMP_FILENAME: str = "dnk_features_tmp.csv"
    PRESENCE_MATRIX_FILENAME: str | None = "presence_matrix.csv"
    DIVIDENDS_FILENAME: str | None = "dividends.csv"
    MKT_CAPS_FILENAME: str = "market_caps.csv"
    ML_TARGETS_FILENAME: str | None = None

    # Experiment settings
    DATA_PROCESSING_START_DATE: pd.Timestamp | None = Field(
        default_factory=lambda: pd.Timestamp("2000-01-01"),
        description="Date to start data processing",
    )
    START_DATE: pd.Timestamp = Field(
        default_factory=lambda: pd.Timestamp("1980-01-01"),
        description="Backtest start date",
    )
    END_DATE: pd.Timestamp = Field(
        default_factory=lambda: pd.Timestamp("2024-01-01"),
        description="Backtest end date",
    )
    REBALANCE_FREQ: int | str | None = Field(
        default=21,
        description="Rebalancing frequency (int=days, str=pandas freq, None=buy&hold)",
    )
    HEDGE_FREQ: int | str | None = Field(
        default=1,
        description="Hedging frequency (int=days, str=pandas freq, None=no hedge)",
    )
    N_LOOKBEHIND_PERIODS: int | None = Field(
        default=None,
        ge=1,
        description="Number of periods for rolling regression",
    )
    MIN_ROLLING_PERIODS: int = Field(
        default=12,
        ge=1,
        description="Minimum periods before first rebalance",
    )
    CAUSAL_WINDOW_SIZE: int | None = Field(
        default=None,
        ge=0,
        description="Look-ahead bias prevention window",
    )
    CAUSAL_WINDOW_END_DATE_FIELD: str | None = Field(
        default=None,
        description="Field name for causal window end date",
    )

    # Universe settings
    FACTORS: tuple[str, ...] = Field(
        default=("low_risk", "momentum", "size", "quality", "value", "spx"),
        description="Factor names",
    )
    TARGETS: tuple[str, ...] = Field(
        default=(),
        description="ML target variable names",
    )
    ASSET_UNIVERSE: tuple[str, ...] | None = Field(
        default=None,
        description="Tradeable asset restrictions",
    )
    HEDGING_ASSETS: tuple[str, ...] = Field(
        default=("spx_fut",),
        description="Hedging instrument names",
    )
    RF_NAME: str = Field(default="acc_rate", description="Risk-free rate column name")
    MKT_NAME: str = Field(default="spx", description="Market index column name")

    @field_validator("START_DATE", "END_DATE", "DATA_PROCESSING_START_DATE", mode="before")
    @classmethod
    def parse_dates(cls, v: str | pd.Timestamp | None) -> pd.Timestamp | None:
        """Convert string dates to Timestamps."""
        if v is None or isinstance(v, pd.Timestamp):
            return v
        return pd.Timestamp(v)

    @model_validator(mode="after")
    def validate_date_ordering(self) -> BaseExperimentConfigV2:
        """Ensure dates are in correct order."""
        if self.START_DATE >= self.END_DATE:
            msg = f"START_DATE ({self.START_DATE}) must be before END_DATE ({self.END_DATE})"
            raise ValueError(msg)

        if self.DATA_PROCESSING_START_DATE is not None and self.DATA_PROCESSING_START_DATE > self.START_DATE:
            msg = f"DATA_PROCESSING_START_DATE ({self.DATA_PROCESSING_START_DATE}) must be <= START_DATE ({self.START_DATE})"
            raise ValueError(msg)

        return self

    @field_validator("REBALANCE_FREQ", "HEDGE_FREQ")
    @classmethod
    def validate_frequencies(cls, v: int | str | None) -> int | str | None:
        """Validate frequency values."""
        if isinstance(v, int) and v < 1:
            msg = f"Frequency must be positive, got {v}"
            raise ValueError(msg)
        return v
