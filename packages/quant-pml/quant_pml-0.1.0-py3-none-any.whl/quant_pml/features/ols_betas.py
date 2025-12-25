from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm


def prepare_data(risk_premia: pd.DataFrame, excess_r: pd.Series) -> tuple[pd.Series, pd.DataFrame]:
    data = pd.merge_asof(
        risk_premia,
        excess_r,
        left_index=True,
        right_index=True,
        tolerance=pd.Timedelta("1D"),
    )
    data = data.dropna(axis=0, how="any")

    y = data[excess_r.name]
    x = data[risk_premia.columns]
    x = sm.add_constant(x)

    return y, x


def get_exposures(
    factors: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    return_residuals: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]:
    # TODO(@V): Speedup by vectorizing regressions as tensors

    betas = pd.DataFrame(index=targets.columns, columns=factors.columns)
    resids = pd.DataFrame(index=targets.index, columns=targets.columns)
    for stock in targets.columns:
        # Stocks should be passed as already excess returns
        xs_r = targets[stock]

        y, x = prepare_data(
            excess_r=xs_r,
            risk_premia=factors,
        )

        if len(x) == 0:
            betas.loc[stock] = np.nan
            resids[stock] = np.nan
        else:
            lr = sm.OLS(y, x)
            results = lr.fit()
            betas.loc[stock] = results.params.loc[betas.columns]
            resids[stock] = results.resid

    if return_residuals:
        return betas, resids

    return betas


def get_betas(market_index: pd.Series, targets: pd.DataFrame) -> pd.Series:
    erp = market_index

    targets_pl = pl.from_pandas(targets, include_index=True).with_columns(pl.col("date").cast(pl.Date))
    erp_pl = pl.from_pandas(erp, include_index=True).with_columns(pl.col("date").cast(pl.Date))
    hedging_column_name = erp.name

    targets_long = targets_pl.unpivot(
        index="date",
        on=targets.columns,
        variable_name="stock",
        value_name="target_return",
    ).sort("date")

    risk_premia_regression_df = targets_long.join_asof(erp_pl, on="date", tolerance="1d")

    betas_df = (
        risk_premia_regression_df.group_by("stock")
        .agg(beta=pl.cov(hedging_column_name, "target_return") / pl.var(hedging_column_name))
        .sort("stock")
    )

    return betas_df.to_pandas().set_index("stock")["beta"]


def get_window_betas(
    market_index: pd.Series,
    targets: pd.DataFrame,
    window_days: int | None,
    *,
    as_trading_days: bool = False,
) -> pd.Series:
    if as_trading_days:
        return get_betas(
            market_index=market_index.iloc[-window_days:],
            targets=targets.iloc[-window_days:],
        )
    first_date = targets.index[-1] - pd.Timedelta(days=window_days) if window_days is not None else None

    return get_betas(
        market_index=market_index.loc[first_date:],
        targets=targets.loc[first_date:],
    )
