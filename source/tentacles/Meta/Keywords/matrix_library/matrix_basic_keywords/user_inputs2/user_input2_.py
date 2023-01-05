import octobot_trading.modes.script_keywords.basic_keywords.user_inputs as user_inputs
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
    return await user_inputs.user_input(
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
