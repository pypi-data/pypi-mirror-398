from __future__ import annotations

from collections.abc import Callable

import gymnasium
import numpy as np
import pandas as pd
from gymnasium import spaces
from imitation.data.wrappers import RolloutInfoWrapper


class BanditEnvironment(gymnasium.Env):
    def __init__(
        self,
        features: pd.DataFrame,
        normalized_curves: pd.DataFrame,
    ) -> None:
        super().__init__()

        self.features = features.astype(np.float32)
        self.normalized_curves = normalized_curves.astype(np.float32)
        self.sampled_actions = self.normalized_curves.columns.astype(np.float32).to_numpy()

        self.action_space = spaces.Box(low=0, high=1, dtype=np.float32)

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(1, self.features.shape[1]),
            dtype=np.float32,
        )

        self.start_dates = self.features.index.to_numpy()

        self.current_id = 0

        self._action_hist = []

    def __len__(self):
        return len(self.start_dates)

    def get_current_id(self):
        return self.current_id

    def reset(self, *args, **kwargs):
        return self.get_context(), {}

    def get_context(self):
        return self.features.iloc[self.current_id].fillna(0).to_numpy().reshape(1, -1)

    def step(self, action: np.array) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
        action = action[0]

        self._action_hist.append([self.start_dates[self.current_id], action])

        current_curve = self.normalized_curves.iloc[self.current_id].to_numpy()
        reward_idx = np.argmin(np.abs(self.sampled_actions - action))
        reward = current_curve[reward_idx]

        self.current_id += 1
        obs = self.get_context()

        done = 1

        return obs, np.array([reward]), np.array([done]), np.array([0.0]), {}

    @property
    def action_hist(self):
        return pd.DataFrame(self._action_hist, columns=["date", "cgp_ucb"]).set_index("date")

    def render(self, mode: str = "human", close: bool = False):
        self.action_hist.plot()


class OptimalEnvironment(gymnasium.Env):
    def __init__(
        self,
        optimal_vol: pd.Series,
        features: pd.DataFrame,
    ) -> None:
        super().__init__()

        self.features = features.astype(np.float32)
        self.optimal_rewards = optimal_vol.astype(np.float32).to_numpy()

        self.action_space = spaces.Box(low=0, high=1, dtype=np.float32)

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(1, self.features.shape[1]),
            dtype=np.float32,
        )

        self.current_id = 0
        self.start_dates = self.features.index.to_numpy()

        self._action_hist = []

    def __len__(self):
        return len(self.features)

    def get_current_id(self):
        return self.current_id

    def reset(self, *args, **kwargs):
        return self.get_context(), {}

    def get_context(self):
        return self.features.iloc[self.current_id].fillna(0).to_numpy().reshape(1, -1)

    def step(self, action: np.array) -> tuple[np.ndarray, float, float, float, dict]:
        action = action[0]

        self._action_hist.append([self.start_dates[self.current_id], action])

        obs = self.get_context()
        reward = self.optimal_rewards[self.current_id]
        done = 1

        self.current_id += 1

        return obs, reward, done, 0.0, {}

    @property
    def action_hist(self):
        return pd.DataFrame(self._action_hist, columns=["date", "cgp_ucb"]).set_index("date")

    def render(self, mode: str = "human", close: bool = False):
        self.action_hist.plot()


# Function to initialize an environment instance
def make_env(
    features: pd.DataFrame,
    normalized_curves: pd.DataFrame,
) -> Callable:
    """Returns a callable that creates an instance of BanditEnvironment.

    Args:
        features: Macro features used for environment initialization.
        normalized_curves: Normalized curves for environment initialization.

    Returns:
        A callable function that creates an environment.

    """

    def _init():
        return BanditEnvironment(features, normalized_curves)

    return _init


# Function to initialize an environment instance
def make_optimal_env(
    optimal_vol: pd.Series,
    features: pd.DataFrame,
) -> Callable:
    """Returns a callable that creates an instance of BanditEnvironment.

    Args:
        optimal_vol: Optimal volatility series.
        features: Macro features used for environment initialization.

    Returns:
        A callable function that creates an environment.

    """

    def _init():
        return RolloutInfoWrapper(OptimalEnvironment(optimal_vol, features))

    return _init
