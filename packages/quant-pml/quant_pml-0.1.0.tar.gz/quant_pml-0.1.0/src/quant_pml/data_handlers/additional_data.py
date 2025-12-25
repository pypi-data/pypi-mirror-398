from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from quant_pml.config.base_experiment_config import BaseExperimentConfig


def add_factors(
    crsp_prices: pd.DataFrame,
    config: BaseExperimentConfig,
) -> pd.DataFrame:
    jkp_factors = pd.read_csv(config.PATH_FACTORS / config.FACTORS_FILENAME)
    jkp_factors["date"] = pd.to_datetime(jkp_factors["date"])
    factors = jkp_factors.pivot_table(index="date", columns="name", values="ret")

    return crsp_prices.merge(factors, left_index=True, right_index=True, how="left")


def add_rf_rate_and_market_index(crsp_prices: pd.DataFrame, config: BaseExperimentConfig) -> pd.DataFrame:
    spx = pd.read_excel(config.PATH_MKT / config.MKT_FILENAME, skiprows=6)
    spx = spx.rename(columns={"Date": "date", "PX_LAST": "spx"})
    spx["date"] = pd.to_datetime(spx["date"])
    spx = spx.set_index("date")
    spx = spx.sort_index()
    spx = spx[["spx"]].ffill().pct_change()

    ff = pd.read_csv(
        config.PATH_RF_RATE / config.RF_RATE_FILENAME,
        engine="python",
        skiprows=4,
        skipfooter=3,
    )
    ff = ff.rename(columns={"Unnamed: 0": "date", "RF": "acc_rate", "Mkt-RF": "mkt-rf"})
    ff["date"] = pd.to_datetime(ff["date"], format="%Y%m%d")
    ff = ff.set_index("date")
    ff = ff / 100

    spx_rf = spx.merge(ff[["acc_rate", "mkt-rf"]], left_index=True, right_index=True, how="outer")
    spx_rf["spx-rf"] = spx_rf["spx"].sub(spx_rf["acc_rate"], axis=0)

    return crsp_prices.merge(spx_rf, left_index=True, right_index=True, how="left")


def add_hedging_assets(crsp_prices: pd.DataFrame, config: BaseExperimentConfig) -> pd.DataFrame:
    spx_fut = pd.read_excel(config.PATH_HEDGING_ASSETS / config.HEDGING_ASSETS_FILENAME, skiprows=6)
    spx_fut = spx_fut.rename(columns={"Date": "date", "PX_LAST": "spx_fut"})
    spx_fut["date"] = pd.to_datetime(spx_fut["date"])
    spx_fut = spx_fut.set_index("date")
    spx_fut = spx_fut.sort_index()

    return crsp_prices.merge(spx_fut["spx_fut"], left_index=True, right_index=True, how="left")
