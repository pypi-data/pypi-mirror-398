############################################################################
### QPMwP - OPTIMIZATION
############################################################################

# --------------------------------------------------------------------------
# Cyril Bachelard
# This version:     18.01.2025
# First version:    18.01.2025
# --------------------------------------------------------------------------


# Standard library imports
from __future__ import annotations

from abc import ABC, abstractmethod

# Third party imports
import numpy as np
import pandas as pd

from quant_pml.optimization.constraints import Constraints

# Local modules
from quant_pml.optimization.helper_functions import to_numpy
from quant_pml.optimization.quadratic_program import QuadraticProgram


class Objective:
    """A class to handle the objective function of an optimization problem.

    Parameters
    ----------
    kwargs: Keyword arguments to initialize the coefficients dictionary. E.g. P, q, constant.

    """

    def __init__(self, **kwargs) -> None:
        self.coefficients = kwargs

    @property
    def coefficients(self) -> dict:
        return self._coefficients

    @coefficients.setter
    def coefficients(self, value: dict) -> None:
        if isinstance(value, dict):
            self._coefficients = value
        else:
            msg = "Input value must be a dictionary."
            raise ValueError(msg)


class OptimizationParameter(dict):
    """A class to handle optimization parameters.

    Parameters
    ----------
    kwargs: Additional keyword arguments to initialize the dictionary.

    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            solver_name="cvxopt",
        )
        self.update(kwargs)


class Optimization(ABC):
    """Abstract base class for optimization problems.

    Parameters
    ----------
    params (OptimizationParameter): Optimization parameters.
    kwargs: Additional keyword arguments.

    """

    def __init__(
        self,
        params: OptimizationParameter | None = None,
        constraints: Constraints | None = None,
        **kwargs,
    ) -> None:
        self.params = OptimizationParameter() if params is None else params
        self.params.update(**kwargs)
        self.constraints = Constraints() if constraints is None else constraints
        self.objective: Objective = Objective()
        self.results = {}

    @abstractmethod
    def set_objective(self, *args, **kwargs) -> None:
        msg = "Method 'set_objective' must be implemented in derived class."
        raise NotImplementedError(msg)

    @abstractmethod
    def solve(self) -> None:
        # TODO:
        # Check consistency of constraints
        # self.check_constraints()

        # Get the coefficients of the objective function
        obj_coeff = self.objective.coefficients
        if "P" not in obj_coeff or "q" not in obj_coeff:
            msg = "Objective must contain 'P' and 'q'."
            raise ValueError(msg)

        # Ensure that P and q are numpy arrays
        obj_coeff["P"] = to_numpy(obj_coeff["P"])
        obj_coeff["q"] = to_numpy(obj_coeff["q"])

        self.solve_qpsolvers()

    def solve_qpsolvers(self) -> None:
        self.model_qpsolvers()
        self.model.solve()

        solution = self.model.results["solution"]
        status = solution.found
        ids = self.constraints.ids
        weights = pd.Series(solution.x[: len(ids)] if status else [None] * len(ids), index=ids)

        self.results.update(
            {
                "weights": weights.to_dict(),
                "status": self.model.results["solution"].found,
            }
        )

    def model_qpsolvers(self) -> None:
        # constraints
        constraints = self.constraints
        GhAb = constraints.to_GhAb()
        lb = constraints.box["lower"].to_numpy() if constraints.box["box_type"] != "NA" else None
        ub = constraints.box["upper"].to_numpy() if constraints.box["box_type"] != "NA" else None

        # Create the optimization model as a QuadraticProgram
        self.model = QuadraticProgram(
            P=self.objective.coefficients["P"],
            q=self.objective.coefficients["q"],
            G=GhAb["G"],
            h=GhAb["h"],
            A=GhAb["A"],
            b=GhAb["b"],
            lb=lb,
            ub=ub,
            solver_settings=self.params,
        )

        # TODO:
        # [ ] Add turnover penalty in the objective
        # [ ] Add turnover constraint
        # [ ] Add leverage constraint


class MeanVarianceOptimizer(Optimization):
    def __init__(
        self,
        constraints: Constraints | None = None,
        risk_aversion: float = 1,
        **kwargs,
    ) -> None:
        super().__init__(constraints=constraints, risk_aversion=risk_aversion, **kwargs)
        self.risk_aversion = risk_aversion

        self.mu = None
        self.covmat = None

    def set_objective(self, mu: pd.Series, covmat: pd.DataFrame) -> None:
        self.objective = Objective(
            q=mu * -1,
            P=covmat * 2 * self.params["risk_aversion"],
        )

        self.mu = mu
        self.covmat = covmat

    def solve(self) -> None:
        GhAb = self.constraints.to_GhAb()
        if GhAb["G"] is None and self.constraints.box["box_type"] == "Unbounded":
            x = 1 / self.risk_aversion * np.linalg.inv(self.covmat) @ self.mu
            x = x / x.sum()

            x = pd.Series(x, index=self.constraints.ids)
            self.results.update(
                {
                    "weights": x.to_dict(),
                    "status": True,
                }
            )
        else:
            return super().solve()
        return None


class VarianceMinimizer(Optimization):
    def __init__(
        self,
        constraints: Constraints,
        **kwargs,
    ) -> None:
        super().__init__(constraints=constraints, **kwargs)

        self.asset_names = constraints.ids

    def set_objective(self, covmat: pd.DataFrame) -> None:
        self.objective = Objective(
            P=covmat,
            q=np.zeros(covmat.shape[0]),
        )

    def solve(self) -> None:
        GhAb = self.constraints.to_GhAb()
        if GhAb["G"] is None and self.constraints.box["box_type"] == "Unbounded":
            A = GhAb["A"]
            b = GhAb["b"]
            # If b is scalar, convert it to a 1D array
            if isinstance(b, (int, float)) or b.ndim == 0:
                b = np.array([b])

            P = self.objective.coefficients["P"]
            P_inv = np.linalg.inv(P)

            AP_invA = A @ P_inv @ A.T
            AP_invA_inv = np.linalg.inv(AP_invA) if AP_invA.shape[0] > 1 else 1 / AP_invA
            x = pd.Series(P_inv @ A.T @ AP_invA_inv @ b, index=self.constraints.ids)
            self.results.update(
                {
                    "weights": x.to_dict(),
                    "status": True,
                }
            )
            return None
        return super().solve()


class CorrelationMinimizer(Optimization):
    def __init__(
        self,
        constraints: Constraints,
        **kwargs,
    ) -> None:
        super().__init__(constraints=constraints, **kwargs)

        self.asset_names = constraints.ids

    def set_objective(self, corr_mat: pd.DataFrame) -> None:
        self.objective = Objective(
            P=corr_mat,
            q=np.zeros(corr_mat.shape[0]),
        )

    def solve(self) -> None:
        return super().solve()
