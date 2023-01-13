import enum


class LivePlottingModes(enum.Enum):
    DISABLE_PLOTTING = "disable live plotting"
    PLOT_RECORDING_MODE = "plot recording mode"
    REPLOT_VISIBLE_HISTORY = "replot visible history"


class BacktestPlottingModes(enum.Enum):
    DISABLE_PLOTTING = "disable backtest plotting"
    ENABLE_PLOTTING = "enable backtest plotting"


class StrategyModes:
    AUTOMATED_BASED_ON_INDICATORS: str = "Automated based on indicators"
    AUTOMATED_PORTFOLIO_BALANCING: str = "Automated portfolio balancing"
    SEMI_AUTOMATED_TRADING: str = "Semi automated trading"
    ALL_MODES: list = [
        AUTOMATED_BASED_ON_INDICATORS,
        AUTOMATED_PORTFOLIO_BALANCING,
        SEMI_AUTOMATED_TRADING,
    ]


class SemiAutoTradeCommands:
    EXECUTE = "execute"
