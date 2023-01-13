import octobot_trading.modes.scripted_trading_mode.abstract_scripted_trading_mode as abstract_scripted_trading_mode
import octobot_trading.enums as trading_enums
import tentacles.Trading.Mode.spot_master_3000_trading_mode.spot_master_3000_trading_mode as spot_master_3000_trading_mode


class SpotMaster3000Mode(abstract_scripted_trading_mode.AbstractScriptedTradingMode):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.producer = SpotMaster3000ModeProducer
        import backtesting_script
        import profile_trading_script

        self.register_script_module(profile_trading_script)
        self.register_script_module(backtesting_script, live=False)

    def get_mode_producer_classes(self) -> list:
        return [SpotMaster3000ModeProducer]

    @classmethod
    def get_supported_exchange_types(cls) -> list:
        """
        :return: The list of supported exchange types
        """
        return [
            trading_enums.ExchangeTypes.SPOT,
        ]


class SpotMaster3000ModeProducer(spot_master_3000_trading_mode.SpotMaster3000Making):
    async def _pre_script_call(self, context, action: dict or str = None) -> None:
        await self.make_strategy(context)

    async def make_strategy(self, ctx) -> None:
        # if not ctx.exchange_manager.is_backtesting:
        #     # live trading
        await self.build_and_trade_strategies_live(ctx)
        # elif not self.trading_mode.get_initialized_trading_pair_by_bot_id(
        #     ctx.symbol, ctx.time_frame
        # ):
        # await self.build_strategies_backtesting_cache(ctx)
        # else:
        #     # back-testing on all the other candles
        #     await self.trade_strategies_backtesting(ctx)
