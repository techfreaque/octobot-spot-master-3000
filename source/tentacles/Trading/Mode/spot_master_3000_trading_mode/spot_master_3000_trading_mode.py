import decimal
import typing

import octobot_trading.api.portfolio as portfolio

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
    limit_buy_offset: float = None
    limit_sell_offset: float = None
    order_type: str = None
    spot_master_name = "spot_master_3000"
    enable_plot_portfolio_p: bool = None
    enable_plot_portfolio_ref: bool = None

    async def build_and_trade_strategies_live(self, ctx):
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
        await self.execute_orders()
        await self.init_plot_settings()
        await self.init_plot_portfolio()
        if self.enable_plot:
            await self.plot_portfolio()
            await trade_analysis_activation.handle_trade_analysis_for_current_candle(
                ctx, self.plot_settings_name
            )

    async def execute_orders(self):
        if SpotMasterOrderTypes.LIMIT.value == self.order_type:
            await cancelling.cancel_orders(self.ctx)

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
            if self.order_type == SpotMasterOrderTypes.LIMIT.value:
                await order_types.limit(
                    self.ctx,
                    side=order_to_execute.change_side,
                    amount=amount,
                    offset=f"@{order_to_execute.order_execute_price}",
                )
            elif self.order_type == SpotMasterOrderTypes.MARKET.value:
                await order_types.market(
                    self.ctx,
                    side=order_to_execute.change_side,
                    amount=amount,
                )

    async def calculate_target_portfolio(self):
        self.target_portfolio = {}
        self.orders_to_execute = []
        for coin, settings in self.target_settings.items():
            if coin not in self.ctx.symbol and coin != self.ref_market:
                continue
            if is_ref_market := self.ref_market == coin:
                asset_value = 1
            else:
                try:
                    asset_value = await exchange_public_data.get_current_candle(
                        self, "close", symbol=f"{coin}/{self.ref_market}"
                    )
                except ValueError:
                    if not self.ctx.exchange_manager.is_backtesting:
                        self.ctx.logger.error(
                            f" Price missing for the candle "
                            f"(time: {self.ctx.trigger_cache_timestamp}, "
                            f"{coin}/{self.ref_market}, {self.ctx.time_frame})"
                        )
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
                limit_buy_offset=self.limit_buy_offset,
                limit_sell_offset=self.limit_sell_offset,
                order_type=self.order_type,
                ref_market=self.ref_market,
            )
            if asset.should_change:
                if is_ref_market:
                    self.ref_market_asset = asset
                else:
                    self.orders_to_execute.append(asset)
            self.target_portfolio[coin] = asset
