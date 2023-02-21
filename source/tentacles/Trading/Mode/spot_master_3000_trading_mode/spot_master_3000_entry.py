import octobot_commons.logging as logging
import octobot_trading.enums as trading_enums
from octobot_trading.modes.script_keywords import context_management
import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.mode.mode_base.abstract_mode_base as abstract_mode_base
import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.mode.spot_master.spot_master_3000_trading_mode as spot_master_3000_trading_mode


class SpotMaster3000Mode(abstract_mode_base.AbstractBaseMode):
    ENABLE_PRO_FEATURES = False
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.producer = SpotMaster3000ModeProducer
        if exchange_manager:
            try:
                import backtesting_script

                self.register_script_module(backtesting_script, live=False)
            except (AttributeError, ModuleNotFoundError):
                pass
            try:
                import profile_trading_script

                self.register_script_module(profile_trading_script)
            except (AttributeError, ModuleNotFoundError):
                pass
        else:
            logging.get_logger(self.get_name()).error(
                "At least one exchange must be enabled to use SpotMaster3000Mode"
            )

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
    async def make_strategy(self, ctx: context_management.Context, action: str):
        self.action = action
        await self.execute_rebalancing_strategy(ctx)
