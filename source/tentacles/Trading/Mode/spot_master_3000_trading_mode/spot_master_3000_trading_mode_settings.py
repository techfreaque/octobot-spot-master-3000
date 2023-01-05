import typing

import octobot_commons.enums as commons_enums
import octobot_commons.symbols.symbol_util as symbol_util

import octobot_trading.modes.script_keywords.basic_keywords.user_inputs as user_inputs
import octobot_trading.api.symbol_data as symbol_data

import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.mode.trading_mode as trading_mode_basis
import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.enums as matrix_enums
import tentacles.Trading.Mode.spot_master_3000_trading_mode.enums as spot_master_enums

try:
    import tentacles.Meta.Keywords.scripting_library.data.writing.plotting as plotting
except (ImportError, ModuleNotFoundError):
    plotting = None


class SpotMaster3000ModeSettings(trading_mode_basis.MatrixMode):
    target_settings: dict = {}
    coins_to_trade: list = []
    ref_market: str = None
    threshold_to_sell: float = None
    threshold_to_buy: float = None
    step_to_sell: float = None
    step_to_buy: float = None
    max_buffer_allocation: float = None
    min_buffer_allocation: float = None
    limit_buy_offset: float = None
    limit_sell_offset: float = None
    spot_master_name = "spot_master_3000"
    order_type = None
    available_coins: list = None
    enable_plot_portfolio_p: bool = None
    enable_plot_portfolio_ref: bool = None
    live_plotting_modes: list = [
        matrix_enums.LivePlottingModes.DISABLE_PLOTTING.value,
        matrix_enums.LivePlottingModes.PLOT_RECORDING_MODE.value,
    ]
    live_plotting_mode: str = matrix_enums.LivePlottingModes.PLOT_RECORDING_MODE.value

    async def init_spot_master_settings(self, ctx) -> None:
        self.ctx = None
        self.ctx = ctx
        self.set_available_coins()
        await user_inputs.user_input(
            self.ctx,
            self.spot_master_name,
            commons_enums.UserInputTypes.OBJECT,
            def_val=None,
            title="SpotMaster 3000 settings",
            other_schema_values={
                "grid_columns": 12,
                "description": "If you have questions, issues, etc, let me know here: "
                "https://github.com/techfreaque/octobot-spot-master-3000",
            },
            show_in_summary=False,
        )
        self.coins_to_trade = await user_inputs.user_input(
            self.ctx,
            "selected_coins",
            commons_enums.UserInputTypes.MULTIPLE_OPTIONS,
            def_val=self.available_coins,
            options=self.available_coins,
            title="Select the coins to trade",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 12,
                "description": "The reference market must be selected and "
                "make sure the allocation for each coin adds up to 100%. ",
            },
        )
        await self.init_balancing_settings()
        await self.init_coin_settings()

    def set_available_coins(self) -> None:
        self.available_coins = self.get_coins_from__all_symbols(
            symbol_data.get_config_symbols(self.ctx.exchange_manager.config, True)
        )

    async def init_balancing_settings(self):

        await self.init_order_type_settings()

        self.threshold_to_sell = await user_inputs.user_input(
            self.ctx,
            "threshold_to_sell",
            commons_enums.UserInputTypes.FLOAT,
            def_val=1,
            title="Threshold to sell in %",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        self.threshold_to_buy = await user_inputs.user_input(
            self.ctx,
            "threshold_to_buy",
            commons_enums.UserInputTypes.FLOAT,
            def_val=1,
            title="Threshold to buy in %",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        self.step_to_sell = await user_inputs.user_input(
            self.ctx,
            "step_to_sell",
            commons_enums.UserInputTypes.FLOAT,
            def_val=1,
            title="Maximum size to sell per coin and candle in %",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        self.step_to_buy = await user_inputs.user_input(
            self.ctx,
            "step_to_buy",
            commons_enums.UserInputTypes.FLOAT,
            def_val=1,
            title="Maximum size to buy per coin and candle in %",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        self.max_buffer_allocation = await user_inputs.user_input(
            self.ctx,
            "max_buffer_allocation",
            commons_enums.UserInputTypes.FLOAT,
            def_val=5,
            title="Maximum allocation buffer in % (allocation + max_allocation)",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        self.min_buffer_allocation = await user_inputs.user_input(
            self.ctx,
            "min_buffer_allocation",
            commons_enums.UserInputTypes.FLOAT,
            def_val=5,
            title="Minimum allocation buffer in % (allocation - min_allocation)",
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )

    async def init_coin_settings(self):
        self.target_settings = {}
        for coin in self.coins_to_trade:
            coin_selector_allocation_name = f"allocation_for_{coin}"
            await user_inputs.user_input(
                self.ctx,
                coin_selector_allocation_name,
                commons_enums.UserInputTypes.OBJECT,
                def_val=None,
                title=f"Settings for {coin}",
                other_schema_values={
                    "grid_columns": 12,
                },
                show_in_summary=False,
            )
            self.target_settings[coin] = {
                "allocation": await user_inputs.user_input(
                    self.ctx,
                    f"allocation_{coin}",
                    commons_enums.UserInputTypes.FLOAT,
                    def_val=100 / len(self.coins_to_trade),
                    options=self.available_coins,
                    title="Select the optimal allocation in %",
                    parent_input_name=coin_selector_allocation_name,
                ),
            }

    async def init_order_type_settings(self):
        self.order_type = await user_inputs.user_input(
            self.ctx,
            "order_type",
            commons_enums.UserInputTypes.OPTIONS,
            def_val=spot_master_enums.SpotMasterOrderTypes.MARKET.value,
            title="Order type",
            options=[
                spot_master_enums.SpotMasterOrderTypes.MARKET.value,
                spot_master_enums.SpotMasterOrderTypes.LIMIT.value,
            ],
            parent_input_name=self.spot_master_name,
            other_schema_values={
                "grid_columns": 4,
                "description": "Market orders will get filled emidiatly, "
                "but have higher fees. While limit orders might not get filled, "
                "but the fees are cheaper.",
            },
        )
        if self.order_type == spot_master_enums.SpotMasterOrderTypes.LIMIT.value:
            self.limit_buy_offset = await user_inputs.user_input(
                self.ctx,
                "limit_buy_offset",
                commons_enums.UserInputTypes.FLOAT,
                def_val=0.5,
                title="Distance in % from current price to buy limit orders",
                parent_input_name=self.spot_master_name,
                other_schema_values={
                    "grid_columns": 4,
                },
            )
            self.limit_sell_offset = await user_inputs.user_input(
                self.ctx,
                "limit_sell_offset",
                commons_enums.UserInputTypes.FLOAT,
                def_val=0.5,
                title="Distance in % from current price to sell limit orders",
                parent_input_name=self.spot_master_name,
                other_schema_values={
                    "grid_columns": 4,
                },
            )

    def get_coins_from__all_symbols(self, symbols) -> typing.Tuple[str, str]:
        self.ref_market = self.ctx.exchange_manager.config["trading"][
            "reference-market"
        ]
        coins = [self.ref_market]
        for symbol in symbols:
            symbol_obj = symbol_util.parse_symbol(symbol)
            if symbol_obj.quote not in coins:
                coins.append(symbol_obj.quote)
            if symbol_obj.base not in coins:
                coins.append(symbol_obj.base)
        return coins

    async def init_plot_portfolio(self):
        self.enable_plot_portfolio_p = await user_inputs.user_input(
            self.ctx,
            "plot_portfolio_p",
            "boolean",
            def_val=True,
            title="Plot portfolio in %",
            show_in_summary=False,
            show_in_optimizer=False,
            parent_input_name=self.plot_settings_name,
        )
        self.enable_plot_portfolio_ref = await user_inputs.user_input(
            self.ctx,
            "plot_portfolio_ref",
            "boolean",
            def_val=True,
            title=f"Plot portfolio in {self.ref_market}",
            show_in_summary=False,
            show_in_optimizer=False,
            parent_input_name=self.plot_settings_name,
        )

    async def plot_portfolio(self):
        if plotting:
            if self.enable_plot_portfolio_ref or self.enable_plot_portfolio_p:
                key = "b-" if self.ctx.exchange_manager.is_backtesting else "l-"
                if self.enable_plot_portfolio_ref:
                    for coin, _portfolio in self.target_portfolio.items():
                        value_key = key + "cb-" + coin
                        await self.ctx.set_cached_value(
                            value=float(_portfolio.current_value), value_key=value_key
                        )
                        await plotting.plot(
                            self.ctx,
                            f"Current {coin} holdings (in {self.ref_market})",
                            cache_value=value_key,
                            chart="sub-chart",
                            color="blue",
                            shift_to_open_candle_time=False,
                            mode="markers",
                        )
                if self.enable_plot_portfolio_p:
                    for coin, _portfolio in self.target_portfolio.items():
                        value_key = key + "cp-" + coin
                        await self.ctx.set_cached_value(
                            value=float(_portfolio.current_percent * 100),
                            value_key=value_key,
                        )
                        await plotting.plot(
                            self.ctx,
                            f"Current {coin} holdings (in %)",
                            cache_value=value_key,
                            chart="sub-chart",
                            color="blue",
                            shift_to_open_candle_time=False,
                            mode="markers",
                        )
