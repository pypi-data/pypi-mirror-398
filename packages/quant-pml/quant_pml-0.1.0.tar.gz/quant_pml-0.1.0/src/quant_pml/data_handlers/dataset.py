from __future__ import annotations

from enum import Enum

from quant_pml.config.jkp_experiment_config import JKPExperimentConfig as JKPConfig
from quant_pml.config.russell_3000_experiment_config import Russell3000ExperimentConfig as Russell3000Config
from quant_pml.config.spx_experiment_config import SPXExperimentConfig as SPXConfig
from quant_pml.config.topn_experiment_config import TopNExperimentConfig as TopNConfig


class Dataset(Enum):
    # TODO(@V): KF Factors, Country ETF, Russia
    SPX_US = SPXConfig
    TOPN_US = TopNConfig
    JKP = JKPConfig

    # Currently mock Russell 3000 by top 3000 largest stocks
    RUSSELL_3000 = Russell3000Config
