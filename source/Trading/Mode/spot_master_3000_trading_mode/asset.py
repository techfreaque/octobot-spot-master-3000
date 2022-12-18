import decimal


class TargetAsset:
    should_change = False
    change_side: str = None
    order_percent: decimal.Decimal = None
    order_value: decimal.Decimal = None
    order_amount: decimal.Decimal = None
    order_execute_price: decimal.Decimal = None

    def __init__(
        self,
        total_value,
        target_percent,
        portfolio,
        asset_value,
        threshold_to_sell,
        threshold_to_buy,
        step_to_sell,
        step_to_buy,
        max_buffer_allocation,
        min_buffer_allocation,
        coin,
        ref_market,
        is_ref_market=False,
    ):
        self.coin = coin
        self.max_buffer_allocation = convert_percent_to_decimal(max_buffer_allocation)
        self.min_buffer_allocation = convert_percent_to_decimal(min_buffer_allocation)
        if is_ref_market:
            self.symbol = ref_market
        else:
            self.symbol = f"{coin}/{ref_market}"
        self.is_ref_market = is_ref_market
        self.asset_value = decimal.Decimal(str(asset_value))
        try:
            self.current_amount = portfolio[coin].total
        except KeyError:
            self.current_amount = decimal.Decimal(0)

        self.portfolio_value = total_value
        self.target_percent = convert_percent_to_decimal(target_percent)
        self.target_value = convert_percent_to_value(
            self.target_percent, self.portfolio_value
        )
        self.target_amount = convert_value_to_amount(
            self.target_value, self.asset_value
        )
        self.current_value = convert_amount_to_value(
            self.current_amount, self.asset_value
        )
        self.current_percent = convert_value_to_percent(
            self.portfolio_value, self.current_value
        )
        self.min_buffer_distance_to_current_percent = (
            self.target_percent - self.current_percent - self.min_buffer_allocation
        )
        self.max_buffer_distance_to_current_percent = (
            self.target_percent + self.min_buffer_allocation - self.current_percent
        )
        self.difference_amount = self.target_amount - self.current_amount
        self.difference_value = self.target_value - self.current_value
        self.difference_percent = self.target_percent - self.current_percent
        self.threshold_to_sell = convert_percent_to_decimal(threshold_to_sell)
        self.threshold_to_buy = convert_percent_to_decimal(threshold_to_buy)
        self.step_to_sell = convert_percent_to_decimal(step_to_sell)
        self.step_to_buy = convert_percent_to_decimal(step_to_buy)
        self.check_if_should_change()
        if self.current_percent > 1:
            test = 1

    def check_if_should_change(self):
        if self.difference_percent < 0:
            if self.difference_percent < -(self.threshold_to_sell):
                self.prepare_sell_order()

        elif self.difference_percent > 0:
            if self.difference_percent > (self.threshold_to_buy):
                self.prepare_buy_order()

    def prepare_sell_order(self):
        self.should_change = True
        self.change_side = "sell"
        if self.difference_percent < -self.step_to_sell:
            if self.max_buffer_distance_to_current_percent < self.step_to_sell:
                self.order_percent = -self.max_buffer_distance_to_current_percent
            else:
                self.order_percent = -self.step_to_sell
        else:
            self.order_percent = self.difference_percent
        self.order_value = convert_percent_to_value(
            self.order_percent, self.portfolio_value
        )
        self.order_amount = convert_value_to_amount(self.order_value, self.asset_value)
        self.order_execute_price = self.asset_value * decimal.Decimal(str(1.01))

    def prepare_buy_order(self):
        self.should_change = True
        self.change_side = "buy"
        if self.difference_percent > self.step_to_buy:
            if self.min_buffer_distance_to_current_percent > self.step_to_buy:
                self.order_percent = self.min_buffer_distance_to_current_percent
            else:
                self.order_percent = self.step_to_buy
        else:
            self.order_percent = self.difference_percent
        self.order_value = convert_percent_to_value(
            self.order_percent, self.portfolio_value
        )
        self.order_amount = convert_value_to_amount(self.order_value, self.asset_value)
        self.order_execute_price = self.asset_value * decimal.Decimal(str(0.99))

    # def finalize_prepare_order(self):


def convert_percent_to_decimal(percent) -> decimal.Decimal:
    return decimal.Decimal(str(percent)) / 100


def convert_percent_to_value(percent, value) -> decimal.Decimal:
    return percent * value


def convert_value_to_percent(total_value, value) -> decimal.Decimal:
    return value / total_value if value else decimal.Decimal("0")


def convert_value_to_amount(value, asset_value) -> decimal.Decimal:
    return value / asset_value


def convert_amount_to_value(amount, asset_value) -> decimal.Decimal:
    return amount * asset_value
