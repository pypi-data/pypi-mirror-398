from __future__ import annotations

import pandas as pd

from quant_pml.stats.helpers.max_drawdown import max_drawdown


def stats_pack(returns: pd.Series[float]) -> pd.DataFrame:
    return pd.DataFrame({"max_drawdown": max_drawdown(returns)})
