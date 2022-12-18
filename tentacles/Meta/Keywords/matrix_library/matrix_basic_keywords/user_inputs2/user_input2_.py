from octobot_trading.modes.script_keywords.basic_keywords.user_inputs import user_input
import octobot_trading.constants as trading_constants


async def user_input2(
    maker,
    indicator,
    name,
    input_type,
    def_val,
    min_val=None,
    max_val=None,
    options=None,
    show_in_summary=True,
    show_in_optimizer=True,
    order=None,
):
    return await user_input(
        maker.ctx,
        name + f" ({indicator.config_path_short})",
        input_type=input_type,
        def_val=def_val,
        min_val=min_val,
        max_val=max_val,
        options=options,
        show_in_summary=show_in_summary,
        show_in_optimizer=show_in_optimizer,
        order=order,
        path=indicator.config_path,
    )


async def set_candles_history_size(
    ctx,
    def_val=trading_constants.DEFAULT_CANDLE_HISTORY_SIZE,
    name=trading_constants.CONFIG_CANDLES_HISTORY_SIZE_TITLE,
    show_in_summary=False,
    show_in_optimizer=False,
    order=999,
):
    return await user_input(
        ctx,
        name,
        "int",
        def_val,
        show_in_summary=show_in_summary,
        show_in_optimizer=show_in_optimizer,
        order=order,
    )
