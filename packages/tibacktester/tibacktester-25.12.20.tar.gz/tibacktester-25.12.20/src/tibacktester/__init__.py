"""Global imports."""

"""Copyright (C) 2023 Edward West. All rights reserved.

This code is licensed under Apache 2.0 with Commons Clause license
(see LICENSE for details).
"""

from tibacktester.cache import (
    clear_caches as clear_caches,
    clear_data_source_cache as clear_data_source_cache,
    clear_indicator_cache as clear_indicator_cache,
    clear_model_cache as clear_model_cache,
    disable_caches as disable_caches,
    disable_data_source_cache as disable_data_source_cache,
    disable_indicator_cache as disable_indicator_cache,
    disable_model_cache as disable_model_cache,
    enable_caches as enable_caches,
    enable_data_source_cache as enable_data_source_cache,
    enable_indicator_cache as enable_indicator_cache,
    enable_model_cache as enable_model_cache,
)
from tibacktester.common import (
    BarData as BarData,
    DataCol as DataCol,
    Day as Day,
    FeeMode as FeeMode,
    PositionMode as PositionMode,
    PriceType as PriceType,
    StopType as StopType,
)
from tibacktester.context import (
    ExecContext as ExecContext,
    ExecSignal as ExecSignal,
    PosSizeContext as PosSizeContext,
)
from tibacktester.config import StrategyConfig as StrategyConfig
from tibacktester.data import (
    Alpaca as Alpaca,
    AlpacaCrypto as AlpacaCrypto,
    YFinance as YFinance,
)
from tibacktester.eval import (
    EvalMetrics as EvalMetrics,
    BootstrapResult as BootstrapResult,
)
from tibacktester.indicator import (
    Indicator as Indicator,
    IndicatorSet as IndicatorSet,
    highest as highest,
    indicator as indicator,
    lowest as lowest,
    returns as returns,
)
from tibacktester.model import (
    ModelLoader as ModelLoader,
    ModelSource as ModelSource,
    ModelTrainer as ModelTrainer,
    model as model,
)
from tibacktester.portfolio import (
    Entry as Entry,
    Order as Order,
    Position as Position,
    Trade as Trade,
)
from tibacktester.scope import (
    disable_logging as disable_logging,
    enable_logging as enable_logging,
    disable_progress_bar as disable_progress_bar,
    enable_progress_bar as enable_progress_bar,
    param as param,
    clear_params as clear_params,
    register_columns as register_columns,
    unregister_columns as unregister_columns,
)
from tibacktester.slippage import RandomSlippageModel as RandomSlippageModel
from tibacktester.strategy import (
    Strategy as Strategy,
    TestResult as TestResult,
)
from tibacktester.vect import (
    cross as cross,
    highv as highv,
    lowv as lowv,
    returnv as returnv,
    sumv as sumv,
)

# Temporary fix for regression in Numba 0.57.0
# https://github.com/numba/numba/issues/8940
# from numba.np.unsafe import ndarray

__version__ = "1.2.12"
