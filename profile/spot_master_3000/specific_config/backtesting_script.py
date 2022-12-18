import octobot_trading.modes.script_keywords.context_management as context_management
try:
    import tentacles.Meta.Keywords.scripting_library.backtesting as backtesting 
except (ImportError, ModuleNotFoundError):
    backtesting = None

async def script(ctx: context_management.Context):
    if backtesting:
        return await backtesting.default_backtesting_analysis_script(ctx)
