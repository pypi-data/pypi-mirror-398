from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

# -*- coding: utf-8 -*-
"""
Created on Sun Sep 11 15:18:30 2021

@author: Patrick Ledoit
"""

# function sigmahat=QIS(Y,k)
#
# Y (N*p): raw data matrix of N iid observations on p random variables
# sigmahat (p*p): invertible covariance matrix estimator
#
# Implements the quadratic-inverse shrinkage (QIS) estimator
#    This is a nonlinear shrinkage estimator derived under the Frobenius loss
#    and its two cousins, Inverse Stein's loss and Mininum Variance loss
#
# If the second (optional) parameter k is absent, not-a-number, or empty,
# then the algorithm demeans the data by default, and adjusts the effective
# sample size accordingly. If the user inputs k = 0, then no demeaning
# takes place; if (s)he inputs k = 1, then it signifies that the data Y has
# already been demeaned.
#
# This version: 01/2021

###########################################################################
# This file is released under the BSD 2-clause license.


# Copyright (c) 2021, Olivier Ledoit and Michael Wolf
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###########################################################################
def _qis(y: pd.DataFrame, shrinkage: float = 1.0, k: int | None = None) -> pd.DataFrame:
    # Pre-Conditions: Y is a valid pd.dataframe and optional arg- k which can be
    #    None, np.nan or int
    # Post-Condition: Sigmahat dataframe is returned

    # Set df dimensions
    n = y.shape[0]  # num of columns
    p = y.shape[1]  # num of rows

    # default setting
    if k is None or math.isnan(k):
        y = y.sub(y.mean(axis=0), axis=1)  # demean
        k = 1

    # vars
    n = n - k  # adjust effective sample size
    c = p / n  # concentration ratio

    # Cov df: sample covariance matrix
    sample = pd.DataFrame(np.matmul(y.T.to_numpy(), y.to_numpy())) / n
    sample = (sample + sample.T) / 2  # make symmetrical

    # Spectral decomp
    lambda1, u = np.linalg.eig(sample)  # use LAPACK routines
    lambda1 = lambda1.real  # clip imaginary part due to rounding error
    u = u.real  # clip imaginary part for eigenvectors

    lambda1 = lambda1.real.clip(min=0)  # reset negative values to 0
    dfu = pd.DataFrame(u, columns=lambda1)  # create df with column names lambda
    #                                        and values u
    dfu = dfu.sort_index(axis=1)  # sort df by column index
    lambda1 = dfu.columns  # recapture sorted lambda

    # COMPUTE Quadratic-Inverse Shrinkage estimator of the covariance matrix
    h = (min(c**2, 1 / c**2) ** 0.35) / p**0.35  # smoothing parameter
    invlambda = 1 / lambda1[max(1, p - n + 1) - 1 : p]  # inverse of (non-null) eigenvalues
    dfl = pd.DataFrame()
    dfl["lambda"] = invlambda
    lj = dfl[np.repeat(dfl.columns.values, min(p, n))]  # like  1/lambda_j
    lj = pd.DataFrame(lj.to_numpy())  # Reset column names
    lj_i = lj.subtract(lj.T)  # like (1/lambda_j)-(1/lambda_i)

    theta = lj.multiply(lj_i).div(lj_i.multiply(lj_i).add(lj.multiply(lj) * h**2)).mean(axis=0)  # smoothed Stein shrinker
    htheta = lj.multiply(lj * h).div(lj_i.multiply(lj_i).add(lj.multiply(lj) * h**2)).mean(axis=0)  # its conjugate
    atheta2 = theta**2 + htheta**2  # its squared amplitude

    if p <= n:  # case where sample covariance matrix is not singular
        delta = 1 / (
            (1 - c) ** 2 * invlambda + 2 * c * (1 - c) * invlambda * theta + c**2 * invlambda * atheta2
        )  # optimally shrunk eigenvalues
        delta = delta.to_numpy()
    else:
        delta0 = 1 / ((c - 1) * np.mean(invlambda.to_numpy()))  # shrinkage of null
        #                                                 eigenvalues
        delta = np.repeat(delta0, p - n)
        delta = np.concatenate((delta, 1 / (invlambda * atheta2)), axis=None)

    delta_qis = delta * (sum(lambda1) / sum(delta))  # preserve trace

    init_delta = delta_qis.copy()
    delta_qis = shrinkage * init_delta + (1 - shrinkage) * lambda1.to_numpy()

    # Apply isotonic regression by (De Nard & Kostovic, 2025)
    smallest = np.min(init_delta[init_delta < lambda1])
    largest = np.max(init_delta[init_delta > lambda1])
    crossing_point = (smallest + largest) / 2

    delta_qis[-1] = np.maximum(delta_qis[-1], crossing_point)
    for i in range(len(delta_qis) - 1)[::-1]:
        if init_delta[i] < lambda1[i]:
            delta_qis[i] = np.maximum(np.minimum(delta_qis[i], delta_qis[i + 1]), crossing_point)
        else:
            delta_qis[i] = np.minimum(np.minimum(delta_qis[i], delta_qis[i + 1]), crossing_point)

    temp1 = dfu.to_numpy()
    temp2 = np.diag(delta_qis)
    temp3 = dfu.T.to_numpy().conjugate()
    # reconstruct covariance matrix
    return pd.DataFrame(np.matmul(np.matmul(temp1, temp2), temp3))


class QISCovEstimator(BaseCovEstimator):
    def __init__(self, shrinkage: float = 1.0) -> None:
        super().__init__()

        self.shrinkage = shrinkage

        self._fitted_vols = None
        self._fitted_corr = None
        self._fitted_cov = None

        self._obs_cov = None

    def _fit(self, training_data: TrainingData) -> None:
        ret = training_data.simple_excess_returns

        self._fitted_cov = _qis(ret, shrinkage=self.shrinkage, k=1)
        self._fitted_cov.index = ret.columns
        self._fitted_cov.columns = ret.columns

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:  # noqa: ARG002
        return self._fitted_cov
