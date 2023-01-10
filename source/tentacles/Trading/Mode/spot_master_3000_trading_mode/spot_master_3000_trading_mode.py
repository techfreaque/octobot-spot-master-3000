import decimal
import time
import typing
import octobot_commons.enums as commons_enums
from octobot_commons.symbols.symbol_util import parse_symbol

import octobot_trading.api.portfolio as portfolio
import octobot_trading.enums as trading_enums
import octobot_trading.modes.script_keywords.context_management as context_management

import tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.data.exchange_public_data as exchange_public_data
import tentacles.Meta.Keywords.scripting_library.orders.cancelling as cancelling
import tentacles.Meta.Keywords.scripting_library.orders.order_types as order_types
from tentacles.Trading.Mode.spot_master_3000_trading_mode.enums import (
    SpotMasterOrderTypes,
)
import tentacles.Trading.Mode.spot_master_3000_trading_mode.spot_master_3000_trading_mode_settings as spot_master_3000_trading_mode_settings
from .asset import TargetAsset

try:
    import tentacles.Meta.Keywords.matrix_library.trade_analysis.trade_analysis_activation as trade_analysis_activation
except (ImportError, ModuleNotFoundError):
    trade_analysis_activation = None


class SpotMaster3000Making(
    spot_master_3000_trading_mode_settings.SpotMaster3000ModeSettings
):
    target_settings: dict = {}
    coins_to_trade: list = []
    open_orders: list = []
    ctx: context_management.Context = None
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
    limit_buy_offset: float = None
    limit_sell_offset: float = None
    order_type: str = None
    spot_master_name = "spot_master_3000"
    enable_plot_portfolio_p: bool = None
    enable_plot_portfolio_ref: bool = None

    async def build_and_trade_strategies_live(
        self, ctx: context_management.Context
    ) -> None:
        await self.init_spot_master_settings(ctx)
        self.portfolio = portfolio.get_portfolio(ctx.exchange_manager)
        self.total_value = (
            ctx.exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.portfolio_current_value
        )
        if self.total_value == decimal.Decimal("0"):
            self.ctx.logger.error(
                "Portfolio Value is not initialized or 0, this candle will be skipped. "
                "This is normal if OctoBot just started"
            )
            return
        await self.calculate_target_portfolio()
        if self.ctx.enable_trading:
            await self.execute_orders()
        await self.init_plot_settings()
        await self.init_plot_portfolio()
        if self.enable_plot:
            await self.plot_portfolio()
            if trade_analysis_activation:
                await trade_analysis_activation.handle_trade_analysis_for_current_candle(
                    ctx, self.plot_settings_name
                )

    async def execute_orders(self) -> None:
        for order_to_execute in self.orders_to_execute:
            if order_to_execute.symbol == self.ctx.symbol:
                available_amount, amount = self.get_available_amount(order_to_execute)
                if self.order_type == SpotMasterOrderTypes.LIMIT.value:
                    if amount := self.round_up_order_amount_if_enabled(
                        available_amount=available_amount,
                        order_amount=amount,
                        order_price=order_to_execute.order_execute_price,
                        symbol=order_to_execute.symbol,
                        order_side=order_to_execute.change_side,
                    ):
                        await order_types.limit(
                            self.ctx,
                            side=order_to_execute.change_side,
                            amount=amount,
                            offset=f"@{order_to_execute.order_execute_price}",
                        )
                elif self.order_type == SpotMasterOrderTypes.MARKET.value:
                    if amount := self.round_up_order_amount_if_enabled(
                        available_amount=available_amount,
                        order_amount=amount,
                        order_price=order_to_execute.asset_value,
                        symbol=order_to_execute.symbol,
                        order_side=order_to_execute.change_side,
                    ):
                        await order_types.market(
                            self.ctx,
                            side=order_to_execute.change_side,
                            amount=amount,
                        )

    async def calculate_target_portfolio(self) -> None:
        self.ref_market = self.ctx.top_level_tentacle.config["trading"][
            "reference-market"
        ]
        self.target_portfolio = {}
        self.orders_to_execute = []

        await self.cancel_expired_orders()
        await self.load_orders()
        for coin, settings in self.target_settings.items():
            open_order_size: decimal.Decimal = decimal.Decimal("0")
            available_symbols: list = self.get_available_symbols(coin)
            is_ref_market: bool = False
            converted_total_value: decimal.Decimal = None
            if not available_symbols:
                if is_ref_market := self.ref_market == coin:
                    symbol: str = coin
                    this_ref_market: str = coin
                    asset_value: float = 1
                else:
                    self.ctx.logger.error(f"No trading pair available for {coin}")
                    continue
            else:
                symbol: str = available_symbols[0]
                this_ref_market: str = parse_symbol(symbol).quote
                if this_ref_market != self.ref_market:
                    potential_conversion_symbols: list = [
                        f"{this_ref_market}/{self.ref_market}",
                        f"{self.ref_market}/{this_ref_market}",
                    ]
                    conversion_value: float = None
                    for _symbol in potential_conversion_symbols:
                        if value := await self.get_asset_value(_symbol):
                            conversion_value = value
                            break
                    converted_total_value = self.total_value / decimal.Decimal(
                        str(conversion_value)
                    )

                open_order_size = self.get_open_order_quantity(symbol)
                if not (asset_value := await self.get_asset_value(symbol)):
                    continue
            asset = TargetAsset(
                total_value=converted_total_value or self.total_value,
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
                limit_buy_offset=self.limit_buy_offset,
                limit_sell_offset=self.limit_sell_offset,
                order_type=self.order_type,
                symbol=symbol,
                ref_market=this_ref_market,
                open_order_size=open_order_size,
            )
            if asset.should_change and symbol == self.ctx.symbol:
                self.orders_to_execute.append(asset)
            self.target_portfolio[coin] = asset

    async def load_orders(self):
        self.open_orders = self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders(
            # symbol=self.ctx.symbol
        )

    async def cancel_expired_orders(self):
        if SpotMasterOrderTypes.LIMIT.value == self.order_type:
            until = int(
                time.time()
                - (
                    commons_enums.TimeFramesMinutes[
                        commons_enums.TimeFrames(self.ctx.time_frame)
                    ]
                    * self.limit_max_age_in_bars
                    * 60
                )
            )
            await cancelling.cancel_orders(
                self.ctx, symbol=self.ctx.symbol, until=until
            )

    def get_open_order_quantity(self, symbol: str):
        open_order_size: decimal.Decimal = decimal.Decimal("0")
        if self.open_orders:
            for order in self.open_orders:
                if order.symbol == symbol:
                    if order.side == trading_enums.TradeOrderSide.BUY:
                        open_order_size += order.origin_quantity
                    else:
                        open_order_size -= order.origin_quantity
        return open_order_size

    async def get_asset_value(self, symbol: str) -> bool or float:
        try:
            return await exchange_public_data.get_current_candle(
                self, "close", symbol=symbol
            )
        except (ValueError, KeyError):
            if not self.ctx.exchange_manager.is_backtesting and self.ctx.enable_trading:
                self.ctx.logger.error(
                    f" Price missing for the candle, this is normal if "
                    "you just started octobot"
                    f"(time: {self.ctx.trigger_cache_timestamp}, "
                    f"{symbol}, {self.ctx.time_frame})"
                )
            return False

    def get_available_symbols(self, coin: str) -> list:
        return list(
            filter(lambda symbol: symbol.startswith(coin), self.available_symbols)
        )

    def get_available_amount(
        self, order_to_execute: TargetAsset
    ) -> typing.Tuple[decimal.Decimal, decimal.Decimal]:
        amount = order_to_execute.order_amount
        try:
            if order_to_execute.change_side == "sell":
                available_amount = self.portfolio[order_to_execute.coin].available
            else:
                available_amount = (
                    self.portfolio[order_to_execute.ref_market].available
                    / order_to_execute.asset_value
                )
        except KeyError:
            available_amount = decimal.Decimal("0")
        if available_amount < amount:
            amount = available_amount
        return available_amount, amount

    def round_up_order_amount_if_enabled(
        self,
        available_amount: decimal.Decimal,
        order_amount: decimal.Decimal,
        order_price: decimal.Decimal,
        symbol: str,
        order_side: str,
    ) -> decimal.Decimal:
        if self.round_orders:
            market_status = self.ctx.exchange_manager.exchange.get_market_status(
                symbol, with_fixer=False
            )
            if (original_order_value := order_amount * order_price) <= (
                fixed_min_value := (
                    min_value := decimal.Decimal(
                        str(market_status["limits"]["cost"]["min"])
                    )
                )
                # rounding issue, rounded order size is to small
                * decimal.Decimal("1.02")
            ):
                minimum_amount = fixed_min_value / order_price
                if not self._check_if_available_funds(
                    available_amount,
                    minimum_amount,
                    symbol,
                    order_side,
                    order_price,
                    min_value,
                ) or self._round_down_order_amount(
                    min_value, original_order_value, symbol, order_side
                ):
                    return decimal.Decimal("0")
                return self._round_up_order_amount(
                    min_value, original_order_value, symbol, order_side, minimum_amount
                )
            # dont round
        return order_amount

    def _check_if_available_funds(
        self,
        available_amount,
        minimum_amount,
        symbol,
        order_side,
        order_price,
        min_value,
    ):
        if available_amount < minimum_amount:
            # not enough funds
            self.ctx.logger.warning(
                f"Not enough available funds to open order ({symbol} | "
                f"{order_side} | available value: {available_amount*order_price} "
                f"{self.get_ref_market_from_symbol(symbol)} | required value: "
                f"{min_value} {self.get_ref_market_from_symbol(symbol)}) "
            )
            return False
        return True

    def _round_up_order_amount(
        self, min_value, original_order_value, symbol, order_side, minimum_amount
    ) -> decimal.Decimal:
        # round up
        self.ctx.logger.info(
            f"Rounding up the order value ({symbol} | {order_side} | order value: "
            f"{original_order_value} {self.get_ref_market_from_symbol(symbol)} | "
            f"rounded value: {min_value} {self.get_ref_market_from_symbol(symbol)}) "
        )
        return minimum_amount

    def _round_down_order_amount(
        self, min_value, original_order_value, symbol, order_side
    ) -> bool:
        if (
            round_orders_max_value := (
                decimal.Decimal(str(self.round_orders_max_value / 100)) * min_value
            )
        ) > original_order_value:
            # round down
            self.ctx.logger.warning(
                f"Order less then minimum value to round up ({symbol} | "
                f"{order_side} | order value: {original_order_value} | "
                f"min value to round up: {round_orders_max_value}) "
            )
            return True
        return False

    def get_ref_market_from_symbol(self, symbol) -> str:
        return parse_symbol(symbol).quote
