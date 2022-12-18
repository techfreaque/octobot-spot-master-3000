import decimal
import typing

import octobot_commons.enums as commons_enums
import octobot_commons.symbols.symbol_util as symbol_util

import octobot_trading.constants as trading_constants
import octobot_trading.modes.script_keywords.basic_keywords.user_inputs as user_inputs
import octobot_trading.personal_data as personal_data
import octobot_trading.api.portfolio as portfolio
import octobot_trading.api.symbol_data as symbol_data
import octobot_trading.enums as trading_enums

import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.data.exchange_public_data as exchange_public_data
import tentacles.Meta.Keywords.matrix_library.strategies_builder.strategy_making.strategy_building as strategy_building
import tentacles.Meta.Keywords.matrix_library.trade_analysis.trade_analysis_activation as trade_analysis_activation
from .asset import TargetAsset

try:
    import tentacles.Meta.Keywords.scripting_library.data.writing.plotting as plotting
except (ImportError, ModuleNotFoundError):
    plotting = None


class SpotMaster3000Making(strategy_building.StrategyMaking):
    target_settings: dict = {}
    coins_to_trade: list = []
    ctx = None
    currencies_values: dict = {}
    target_portfolio: dict = {}
    portfolio: dict = {}
    total_value: decimal.Decimal = None
    ref_market: str = None
    ref_market_asset: str = None
    orders_to_execute: typing.List[TargetAsset] = []
    threshold_to_sell: float = None
    threshold_to_buy: float = None
    step_to_sell: float = None
    step_to_buy: float = None
    max_buffer_allocation: float = None
    min_buffer_allocation: float = None

    async def build_and_trade_strategies_live(self, ctx):
        await self.init_trade_analysis(ctx)

        self.ctx = ctx
        # await cancel_orders(self.ctx)
        await self.coin_selector()
        self.portfolio = portfolio.get_portfolio(ctx.exchange_manager)
        self.total_value = (
            ctx.exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.portfolio_current_value
        )
        if self.total_value == decimal.Decimal("0"):
            self.ctx.logger.error(
                "Portfolio Value is not initialized or 0, this candle will be skipped"
            )
            return
        await self.calculate_target_portfolio()
        await self.execute_orders()
        if plotting:
            await trade_analysis_activation.handle_trade_analysis_for_current_candle(
                ctx, self
            )
            await self.plot_portfolio()

    async def execute_orders(self):
        for order_to_execute in self.orders_to_execute:
            if order_to_execute.symbol != self.ctx.symbol:
                continue
            if order_to_execute.order_amount < 0:
                amount = order_to_execute.order_amount * -1
                if (
                    available_to_sell := self.portfolio[order_to_execute.coin].available
                ) < amount:
                    amount = available_to_sell
            else:
                amount = order_to_execute.order_amount
                if (
                    available_to_buy := (
                        self.portfolio[self.ref_market].available
                        / order_to_execute.asset_value
                    )
                ) < amount:
                    amount = available_to_buy
            if order_to_execute.change_side == "buy":
                await self.create_market_order(
                    order_quantity=amount,
                    order_type=trading_enums.TraderOrderType.BUY_MARKET,
                )
            else:
                await self.create_market_order(
                    order_quantity=amount,
                    order_type=trading_enums.TraderOrderType.SELL_MARKET,
                )

    async def create_market_order(
        self,
        order_quantity,
        order_price=None,
        order_type=trading_enums.TraderOrderType.BUY_MARKET,
    ):
        _, _, _, current_price, symbol_market = await personal_data.get_pre_order_data(
            self.ctx.exchange_manager,
            symbol=self.ctx.symbol,
            timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT,
        )
        for (
            final_order_quantity,
            final_order_price,
        ) in personal_data.decimal_check_and_adapt_order_details_if_necessary(
            order_quantity, order_price or current_price, symbol_market, truncate=True
        ):
            created_order = personal_data.create_order_instance(
                trader=self.ctx.trader,
                order_type=order_type,
                symbol=self.ctx.symbol,
                current_price=current_price,
                quantity=final_order_quantity,
                price=final_order_price,
            )
            created_order = await self.ctx.trader.create_order(created_order)
            self.ctx.just_created_orders.append(created_order)

    async def calculate_target_portfolio(self):
        self.target_portfolio = {}
        self.orders_to_execute = []
        for coin, settings in self.target_settings.items():

            if is_ref_market := self.ref_market == coin:
                asset_value = 1
            else:
                try:
                    asset_value = await exchange_public_data.get_current_candle(
                        self, "close", symbol=f"{coin}/{self.ref_market}"
                    )
                except ValueError:
                    # self.ctx.logger.error(
                    #     f" Price missing for the candle "
                    #     f"(time: {self.ctx.trigger_cache_timestamp}, "
                    #     f"{coin}/{self.ref_market}, {self.ctx.time_frame})"
                    # )
                    continue
            asset = TargetAsset(
                total_value=self.total_value,
                target_percent=settings["allocation"],
                portfolio=self.portfolio,
                asset_value=asset_value,
                threshold_to_sell=self.threshold_to_sell,
                threshold_to_buy=self.threshold_to_buy,
                step_to_sell=self.step_to_sell,
                step_to_buy=self.step_to_buy,
                max_buffer_allocation=self.max_buffer_allocation,
                min_buffer_allocation=self.min_buffer_allocation,
                is_ref_market=is_ref_market,
                coin=coin,
                ref_market=self.ref_market,
            )
            if asset.should_change:
                if is_ref_market:
                    self.ref_market_asset = asset
                else:
                    self.orders_to_execute.append(asset)
            self.target_portfolio[coin] = asset

    async def coin_selector(self) -> None:
        all_coins = self.get_coins_from__all_symbols(
            symbol_data.get_config_symbols(self.ctx.exchange_manager.config, True)
        )
        spot_master_name = "spot_master_name"
        await user_inputs.user_input(
            self.ctx,
            spot_master_name,
            commons_enums.UserInputTypes.OBJECT,
            def_val=None,
            title="SpotMaster 3000 settings",
            other_schema_values={"grid_columns": 12, "description": ""},
        )
        coin_selector_name = "coin_selector"
        await user_inputs.user_input(
            self.ctx,
            coin_selector_name,
            commons_enums.UserInputTypes.OBJECT,
            def_val=None,
            title="Coins to hold",
            other_schema_values={
                "grid_columns": 12,
            },
        )
        self.coins_to_trade = await user_inputs.user_input(
            self.ctx,
            coin_selector_name,
            commons_enums.UserInputTypes.MULTIPLE_OPTIONS,
            def_val=all_coins,
            options=all_coins,
            title="Select the coins to hold",
            parent_input_name=coin_selector_name,
            other_schema_values={
                "grid_columns": 12,
            },
        )
        all_coins_settings_name = "all_coins_settings"
        await user_inputs.user_input(
            self.ctx,
            all_coins_settings_name,
            commons_enums.UserInputTypes.OBJECT,
            def_val=None,
            title="Settings for all coins",
            other_schema_values={
                "grid_columns": 12,
            },
        )
        self.threshold_to_sell = await user_inputs.user_input(
            self.ctx,
            "threshold_to_sell",
            commons_enums.UserInputTypes.FLOAT,
            def_val=1,
            title="Threshold to sell in %",
            parent_input_name=all_coins_settings_name,
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
            parent_input_name=all_coins_settings_name,
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
            parent_input_name=all_coins_settings_name,
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
            parent_input_name=all_coins_settings_name,
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
            parent_input_name=all_coins_settings_name,
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
            parent_input_name=all_coins_settings_name,
            other_schema_values={
                "grid_columns": 4,
            },
        )
        self.target_settings = {}
        for coin in self.coins_to_trade:
            coin_selector_allocation_name = f"coin_selector_allocation_{coin}"
            await user_inputs.user_input(
                self.ctx,
                coin_selector_allocation_name,
                commons_enums.UserInputTypes.OBJECT,
                def_val=None,
                title=f"Settings for {coin}",
                other_schema_values={
                    "grid_columns": 12,
                },
            )
            self.target_settings[coin] = {
                "allocation": await user_inputs.user_input(
                    self.ctx,
                    f"allocation_{coin}",
                    commons_enums.UserInputTypes.FLOAT,
                    def_val=100 / len(self.coins_to_trade),
                    options=all_coins,
                    title="Select the optimal allocation in %",
                    parent_input_name=coin_selector_allocation_name,
                ),
            }

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

    async def plot_portfolio(self):
        plot_settings_name = "plot_settings"
        await user_inputs.user_input(
            self.ctx,
            plot_settings_name,
            commons_enums.UserInputTypes.OBJECT,
            def_val=None,
            title="Plot settings",
        )
        enable_plot_portfolio_p = await user_inputs.user_input(
            self.ctx,
            "plot_portfolio_p",
            "boolean",
            def_val=True,
            title="Plot portfolio in %",
            show_in_summary=False,
            show_in_optimizer=False,
            parent_input_name=plot_settings_name,
        )
        enable_plot_portfolio_ref = await user_inputs.user_input(
            self.ctx,
            "plot_portfolio_ref",
            "boolean",
            def_val=True,
            title=f"Plot portfolio in {self.ref_market}",
            show_in_summary=False,
            show_in_optimizer=False,
            parent_input_name=plot_settings_name,
        )
        if enable_plot_portfolio_ref or enable_plot_portfolio_p:
            key = "b-" if self.ctx.exchange_manager.is_backtesting else "l-"
            if enable_plot_portfolio_ref:
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
            if enable_plot_portfolio_p:
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
