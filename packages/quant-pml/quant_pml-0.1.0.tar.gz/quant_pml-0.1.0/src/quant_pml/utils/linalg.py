from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

import numpy as np


def avg_non_diagonal_elements(corr_matrix: pd.DataFrame) -> pd.DataFrame:
    """Compute the average of non-diagonal elements in each correlation matrix."""
    # Select the non-diagonal elements using numpy
    non_diag = corr_matrix.to_numpy()[np.triu_indices_from(corr_matrix, k=1)]
    return np.nanmean(non_diag)


def avg_corr(rolling_window: pd.DataFrame) -> pd.DataFrame:
    # Compute the correlation matrix for the rolling window
    corr_matrix = rolling_window.corr()

    # Compute the average of non-diagonal elements
    return avg_non_diagonal_elements(corr_matrix)


def corr_matrix_from_cov(var_covar: np.ndarray) -> np.ndarray:
    diag_inv = np.diag(1 / np.sqrt(np.diag(var_covar)))
    return diag_inv @ var_covar @ diag_inv


def var_covar_from_corr_array(corr_array: np.ndarray, volatilities: np.ndarray) -> np.ndarray:
    return volatilities @ corr_array @ volatilities


def var_covar_from_corr_array_mac(corr_array: np.ndarray, volatilities: np.ndarray) -> np.ndarray:
    # Use np.dot() due to Apple Silicon chip issues in numpy
    return np.dot(np.dot(volatilities, corr_array), volatilities)


def covmat_from_corr_mat(corr_mat: np.ndarray, volatilities: np.ndarray) -> np.ndarray:
    return np.diag(volatilities) @ corr_mat @ np.diag(volatilities).T
