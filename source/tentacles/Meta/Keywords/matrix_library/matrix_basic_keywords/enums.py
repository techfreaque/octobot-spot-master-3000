import enum


class LivePlottingModes(enum.Enum):
    DISABLE_PLOTTING = "disable live plotting"
    PLOT_RECORDING_MODE = "plot recording mode"
    REPLOT_VISIBLE_HISTORY = "replot visible history"


class BacktestPlottingModes(enum.Enum):
    DISABLE_PLOTTING = "disable backtest indicator plotting"
    ENABLE_PLOTTING = "enable backtest indicator plotting"

CURRENT_TIME_FRAME = "current time frame"
