from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


class OnlineOLSBetas:
    def __init__(self) -> None:
        super().__init__()

        self._x_avg = {}
        self._y_avg = {}
        self._Sxy = {}
        self._Sx = {}
        self._n = {}

        self._beta = None
        self._last_fitted_date = None

    @staticmethod
    def _lr(  # noqa: PLR0913
        x_avg: pd.Series,
        y_avg: pd.Series,
        sxy: pd.Series,
        sx: pd.Series,
        n: pd.Series,
        new_x: pd.DataFrame | np.ndarray,
        new_y: pd.DataFrame | np.ndarray,
    ) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        # Ensure Series input types
        if not isinstance(x_avg, pd.Series):
            x_avg = pd.Series(x_avg)
        if not isinstance(y_avg, pd.Series):
            y_avg = pd.Series(y_avg)
        if not isinstance(sxy, pd.Series):
            sxy = pd.Series(sxy)
        if not isinstance(sx, pd.Series):
            sx = pd.Series(sx)
        if not isinstance(n, pd.Series):
            # broadcast scalar or array-like to Series using x_avg index
            n = pd.Series(n, index=x_avg.index)

        idx = x_avg.index

        # Coerce new_x/new_y to DataFrames aligned on columns = tickers
        if isinstance(new_x, np.ndarray):
            new_x = pd.DataFrame(new_x, columns=idx)
        elif isinstance(new_x, pd.Series):
            # single column series for one ticker
            new_x = new_x.to_frame().reindex(columns=idx)
        else:
            new_x = new_x.reindex(columns=idx)

        if isinstance(new_y, np.ndarray):
            new_y = pd.DataFrame(new_y, columns=idx)
        elif isinstance(new_y, pd.Series):
            new_y = new_y.to_frame().reindex(columns=idx)
        else:
            new_y = new_y.reindex(columns=idx)

        m = new_x.shape[0]
        new_n = n + m

        sum_x = new_x.sum(axis=0)
        sum_y = new_y.sum(axis=0)

        new_x_avg = (x_avg * n + sum_x) / new_n.replace(0, np.nan)
        new_y_avg = (y_avg * n + sum_y) / new_n.replace(0, np.nan)

        # x_star and y_star depend on whether we had previous samples per ticker
        mask_prev = n > 0
        sqrt_n = np.sqrt(n.astype(float))
        sqrt_new_n = np.sqrt(new_n.astype(float))
        denom = sqrt_n + sqrt_new_n

        x_star = pd.Series(index=idx, dtype=float)
        y_star = pd.Series(index=idx, dtype=float)

        x_star[mask_prev] = (x_avg[mask_prev] * sqrt_n[mask_prev] + new_x_avg[mask_prev] * sqrt_new_n[mask_prev]) / denom[
            mask_prev
        ]
        y_star[mask_prev] = (y_avg[mask_prev] * sqrt_n[mask_prev] + new_y_avg[mask_prev] * sqrt_new_n[mask_prev]) / denom[
            mask_prev
        ]
        x_star[~mask_prev] = new_x_avg[~mask_prev]
        y_star[~mask_prev] = new_y_avg[~mask_prev]

        # Update Sx and Sxy using vectorized column-wise operations
        dx = new_x.sub(x_star, axis=1)
        dy = new_y.sub(y_star, axis=1)

        new_sx = sx + (dx**2).sum(axis=0)
        new_sxy = sxy + (dx.mul(dy)).sum(axis=0)

        # Compute regression coefficients per ticker
        beta = new_sxy / new_sx.replace(0, np.nan)
        alpha = new_y_avg - beta * new_x_avg

        return new_sxy, new_sx, new_n, alpha, beta, new_x_avg, new_y_avg

    def fit(self, market_index: pd.DataFrame, y: pd.Series) -> None:  # noqa: ARG002
        return


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
    # TODO(@V): Depreciate and use get_exposures()

    # Index should be passed as already excess returns
    erp = market_index

    betas = pd.DataFrame(index=targets.columns, columns=[market_index.name])
    for stock in targets.columns:
        # Stocks should be passed as already excess returns
        xs_r = targets[stock]

        y, x = prepare_data(
            excess_r=xs_r,
            risk_premia=erp.to_frame(),
        )

        if len(x) == 0:
            beta = 1.0
        else:
            lr = sm.OLS(y, x).fit()
            beta = lr.params.loc[erp.name].item()

        if np.isnan(beta):
            msg = f"Beta for {stock} is NaN."
            raise ValueError(msg)

        betas.loc[stock] = beta

    return betas.iloc[:, 0]


def get_window_betas(market_index: pd.Series, targets: pd.DataFrame, window_days: int | None) -> pd.Series:
    first_date = targets.index[-1] - pd.Timedelta(days=window_days) if window_days is not None else None

    return get_betas(
        market_index=market_index.loc[first_date:],
        targets=targets.loc[first_date:],
    )
