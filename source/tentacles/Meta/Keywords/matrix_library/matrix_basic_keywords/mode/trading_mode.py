import octobot_commons.enums as commons_enums
import octobot_trading.modes.script_keywords.basic_keywords as basic_keywords
import octobot_trading.modes.scripted_trading_mode.abstract_scripted_trading_mode as abstract_scripted_trading_mode
import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.enums as matrix_enums
import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.tools.utilities as utilities
import tentacles.Meta.Keywords.scripting_library.data.writing.plotting as plotting


class MatrixMode(abstract_scripted_trading_mode.AbstractScriptedTradingModeProducer):
    plot_settings_name = "plot_settings"
    default_live_plotting_mode: str = (
        matrix_enums.LivePlottingModes.PLOT_RECORDING_MODE.value
    )
    default_backtest_plotting_mode: str = (
        matrix_enums.BacktestPlottingModes.DISABLE_PLOTTING.value
    )
    live_plotting_modes: list = [
        matrix_enums.LivePlottingModes.DISABLE_PLOTTING.value,
        matrix_enums.LivePlottingModes.REPLOT_VISIBLE_HISTORY.value,
        matrix_enums.LivePlottingModes.PLOT_RECORDING_MODE.value,
    ]
    backtest_plotting_modes: list = [
        matrix_enums.BacktestPlottingModes.ENABLE_PLOTTING.value,
        matrix_enums.BacktestPlottingModes.DISABLE_PLOTTING.value,
    ]

    backtest_plotting_mode: str = None
    live_plotting_mode: str = None

    enable_plot: bool = False

    # todo remove
    live_recording_mode: bool = None
    trigger_time_frames: list = None

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.candles_manager: dict = {}
        self.ctx = None
        self.candles: dict = {}

    async def _register_and_apply_required_user_inputs(self, context):
        if context.exchange_manager.is_future:
            await basic_keywords.set_leverage(
                context, await basic_keywords.user_select_leverage(context)
            )

        # register activating topics user input
        activation_topic_values = [
            commons_enums.ActivationTopics.FULL_CANDLES.value,
            commons_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value,
        ]
        await basic_keywords.get_activation_topics(
            context,
            commons_enums.ActivationTopics.FULL_CANDLES.value,
            activation_topic_values,
        )

    async def build_and_trade_strategies_live(self):
        m_time = utilities.start_measure_time()

        utilities.end_measure_live_time(self.ctx, m_time, " matrix mode - live trading")

    async def build_strategies_backtesting_cache(self):
        s_time = utilities.start_measure_time(
            " matrix mode - building backtesting cache"
        )

        utilities.end_measure_time(
            s_time,
            f" matrix mode - building strategy for "
            f"{self.ctx.time_frame} {len(self.any_trading_timestamps)} trades",
        )

    async def trade_strategies_backtesting(self):
        m_time = utilities.start_measure_time()

        utilities.end_measure_time(
            m_time,
            " matrix mode - warning backtesting candle took longer than expected",
            min_duration=1,
        )

    async def init_plot_settings(self):
        await basic_keywords.user_input(
            self.ctx,
            self.plot_settings_name,
            commons_enums.UserInputTypes.OBJECT,
            def_val=None,
            title="Plot settings",
            show_in_summary=False,
            show_in_optimizer=False,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        await self.init_plotting_modes(self.plot_settings_name, self.plot_settings_name)

    async def init_plotting_modes(self, live_parent_input, backtesting_parent_input):
        self.backtest_plotting_mode = await basic_keywords.user_input(
            self.ctx,
            "backtest_plotting_mode",
            commons_enums.UserInputTypes.OPTIONS,
            title="Backtest plotting mode",
            def_val=self.default_backtest_plotting_mode,
            options=self.backtest_plotting_modes,
            show_in_summary=False,
            show_in_optimizer=False,
            parent_input_name=backtesting_parent_input,
        )
        if self.exchange_manager.is_backtesting:
            if (
                self.backtest_plotting_mode
                == matrix_enums.BacktestPlottingModes.DISABLE_PLOTTING.value
            ):
                self.enable_plot = False
            elif (
                self.backtest_plotting_mode
                == matrix_enums.BacktestPlottingModes.ENABLE_PLOTTING.value
            ):
                self.enable_plot = True
        else:
            self.live_plotting_mode = await basic_keywords.user_input(
                self.ctx,
                "live_plotting_mode",
                commons_enums.UserInputTypes.OPTIONS,
                title="Live plotting mode",
                def_val=self.default_live_plotting_mode,
                options=self.live_plotting_modes,
                show_in_summary=False,
                show_in_optimizer=False,
                parent_input_name=live_parent_input,
            )
            if (
                self.live_plotting_mode
                == matrix_enums.LivePlottingModes.PLOT_RECORDING_MODE.value
            ):
                self.live_recording_mode = True
                self.enable_plot = True
            elif (
                self.live_plotting_mode
                == matrix_enums.LivePlottingModes.DISABLE_PLOTTING.value
            ):
                self.enable_plot = False
                self.live_recording_mode = True
                plotting.disable_candles_plot(self.ctx)
            elif (
                self.live_plotting_mode
                == matrix_enums.LivePlottingModes.REPLOT_VISIBLE_HISTORY.value
            ):
                self.live_recording_mode = False
                self.enable_plot = True
