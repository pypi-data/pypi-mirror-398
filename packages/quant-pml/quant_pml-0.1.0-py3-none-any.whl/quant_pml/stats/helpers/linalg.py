from __future__ import annotations

import numpy as np


def corr_matrix_from_cov(var_covar: np.ndarray) -> np.ndarray:
    diag_inv = np.diag(1 / np.sqrt(np.diag(var_covar)))
    return diag_inv @ var_covar @ diag_inv  # type: ignore[no-any-return]


def var_covar_from_corr_array(corr_array: np.ndarray, volatilities: np.ndarray | None = None) -> np.ndarray:
    if volatilities is None:
        volatilities = np.ones_like(corr_array)
    return volatilities @ corr_array @ volatilities  # type: ignore[no-any-return]
