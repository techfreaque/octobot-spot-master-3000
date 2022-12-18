import octobot_commons.enums as commons_enums
from octobot_trading.modes.script_keywords import basic_keywords
from octobot_trading.modes.scripted_trading_mode import abstract_scripted_trading_mode

from tentacles.Meta.Keywords.matrix_library.strategies_builder.key_words.tools.utilities import (
    start_measure_time,
    end_measure_time,
    end_measure_live_time,
)


class MatrixMode(abstract_scripted_trading_mode.AbstractScriptedTradingModeProducer):
    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.trade_analysis_activated = False

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

    async def build_and_trade_strategies_live(self, ctx):
        m_time = start_measure_time()

        end_measure_live_time(ctx, m_time, " matrix mode - live trading")

    async def build_strategies_backtesting_cache(self, ctx):
        s_time = start_measure_time(" matrix mode - building backtesting cache")

        end_measure_time(
            s_time,
            f" matrix mode - building strategy for "
            f"{ctx.time_frame} {len(self.any_trading_timestamps)} trades",
        )

    async def trade_strategies_backtesting(self, ctx):
        m_time = start_measure_time()

        end_measure_time(
            m_time,
            " matrix mode - warning backtesting candle took longer than expected",
            min_duration=1,
        )

    async def init_trade_analysis(self, ctx):
        self.trade_analysis_activated = await basic_keywords.user_input(
            ctx,
            "enable_trades_plots",
            "boolean",
            title="enable trades/orders/positions plotting function "
            "(very slow together with backtesting plots)",
            def_val=True,
            show_in_summary=False,
        )
