from octobot_trading import exchange_data
import octobot_backtesting.api as backtesting_api
import octobot_commons.enums as commons_enums
import octobot_trading.api as trading_api
from tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.user_inputs2 import (
    user_input2,
)
from tentacles.Meta.Keywords.matrix_library.matrix_basic_keywords.tools.utilities import (
    start_measure_time,
    end_measure_time,
)


async def user_select_candle_source_name(
    maker,
    indicator,
    name="Select Candle Source",
    def_val="close",
    enable_volume=False,
    show_in_summary=False,
    show_in_optimizer=False,
    order=None,
):
    available_data_src = [
        "open",
        "high",
        "low",
        "close",
        "hl2",
        "hlc3",
        "ohlc4",
        "Heikin Ashi open",
        "Heikin Ashi high",
        "Heikin Ashi low",
        "Heikin Ashi close",
    ]
    if enable_volume:
        available_data_src.append("volume")

    source_name = await user_input2(
        maker,
        indicator,
        name,
        "options",
        def_val,
        options=available_data_src,
        show_in_summary=show_in_summary,
        show_in_optimizer=show_in_optimizer,
        order=order,
    )
    return source_name


async def get_candles_(maker, source_name="close", time_frame=None, symbol=None):
    symbol = symbol or maker.ctx.symbol
    time_frame = time_frame or maker.ctx.time_frame
    try:
        return maker.candles[symbol][source_name]
    except KeyError:
        sm_time = start_measure_time()
        if symbol not in maker.candles:
            maker.candles[symbol] = {}
        maker.candles[symbol][source_name] = await _get_candles_from_name(
            maker,
            source_name=source_name,
            time_frame=time_frame,
            symbol=symbol,
            max_history=True,
        )
        end_measure_time(
            sm_time, f" strategy maker - loading candle: {source_name}", min_duration=1
        )
    return maker.candles[symbol][source_name]


async def get_current_candle(
    maker, source_name="close", time_frame=None, symbol=None
) -> float:
    symbol = symbol or maker.ctx.symbol
    time_frame = time_frame or maker.ctx.time_frame
    times = await get_candles_(
        maker, source_name="time", time_frame=time_frame, symbol=symbol
    )
    candles = await get_candles_(
        maker, source_name=source_name, time_frame=time_frame, symbol=symbol
    )
    try:
        current_index = times.index(maker.ctx.trigger_cache_timestamp)
    except ValueError as error:
        raise ValueError(
            f"Price for the candle (time: {maker.ctx.trigger_cache_timestamp}, "
            f"{symbol}, {time_frame})"
        ) from error
    return candles[current_index]


async def _get_candles_from_name(
    maker, source_name, time_frame, symbol, max_history=True
):
    symbol = symbol or maker.ctx.symbol
    time_frame = time_frame or maker.ctx.time_frame
    maker.candles_manager = maker.candles_manager or await _load_candles_manager(
        maker.ctx, symbol, time_frame, max_history
    )
    if source_name == "close":
        return maker.candles_manager.get_symbol_close_candles(-1)
    if source_name == "open":
        return maker.candles_manager.get_symbol_open_candles(-1)
    if source_name == "high":
        return maker.candles_manager.get_symbol_high_candles(-1)
    if source_name == "low":
        return maker.candles_manager.get_symbol_low_candles(-1)
    if source_name == "volume":
        return maker.candles_manager.get_symbol_volume_candles(-1)
    if source_name == "time":
        return maker.candles_manager.get_symbol_time_candles(-1)
    if source_name == "hl2":
        try:
            from tentacles.Evaluator.Util.candles_util import CandlesUtil

            return CandlesUtil.HL2(
                await get_candles_(
                    maker, source_name="high", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="low", time_frame=time_frame, symbol=symbol
                ),
            )
        except ImportError:
            raise RuntimeError("CandlesUtil tentacle is required to use HL2")
    if source_name == "hlc3":
        try:
            from tentacles.Evaluator.Util.candles_util import CandlesUtil

            return CandlesUtil.HLC3(
                await get_candles_(
                    maker, source_name="high", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="low", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="close", time_frame=time_frame, symbol=symbol
                ),
            )
        except ImportError:
            raise RuntimeError("CandlesUtil tentacle is required to use HLC3")
    if source_name == "ohlc4":
        try:
            from tentacles.Evaluator.Util.candles_util import CandlesUtil

            return CandlesUtil.OHLC4(
                await get_candles_(
                    maker, source_name="open", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="high", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="low", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="close", time_frame=time_frame, symbol=symbol
                ),
            )
        except ImportError:
            raise RuntimeError("CandlesUtil tentacle is required to use OHLC4")
    if "Heikin Ashi" in source_name:
        try:
            from tentacles.Evaluator.Util.candles_util import CandlesUtil

            haOpen, haHigh, haLow, haClose = CandlesUtil.HeikinAshi(
                await get_candles_(
                    maker, source_name="open", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="high", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="low", time_frame=time_frame, symbol=symbol
                ),
                await get_candles_(
                    maker, source_name="close", time_frame=time_frame, symbol=symbol
                ),
            )
            maker.candles["Heikin Ashi open"] = haOpen
            maker.candles["Heikin Ashi high"] = haHigh
            maker.candles["Heikin Ashi low"] = haLow
            maker.candles["Heikin Ashi close"] = haClose
            if source_name == "Heikin Ashi close":
                return haClose
            if source_name == "Heikin Ashi open":
                return haOpen
            if source_name == "Heikin Ashi high":
                return haHigh
            if source_name == "Heikin Ashi low":
                return haLow
        except ImportError:
            raise RuntimeError("CandlesUtil tentacle is required to use Heikin Ashi")


async def _load_backtesting_candles_manager(
    exchange_manager,
    symbol: str,
    time_frame: str,
) -> exchange_data.CandlesManager:
    start_time = backtesting_api.get_backtesting_starting_time(
        exchange_manager.exchange.backtesting
    )
    end_time = backtesting_api.get_backtesting_ending_time(
        exchange_manager.exchange.backtesting
    )
    ohlcv_data: list = await exchange_manager.exchange.exchange_importers[0].get_ohlcv(
        exchange_name=exchange_manager.exchange_name,
        symbol=symbol,
        time_frame=commons_enums.TimeFrames(time_frame),
    )
    chronological_candles: list = sorted(ohlcv_data, key=lambda candle: candle[0])
    full_candles_history = [
        ohlcv[-1]
        for ohlcv in chronological_candles
        if start_time <= ohlcv[0] <= end_time
    ]
    candles_manager = exchange_data.CandlesManager(
        max_candles_count=len(full_candles_history)
    )
    await candles_manager.initialize()
    candles_manager.replace_all_candles(full_candles_history)
    return candles_manager


async def _load_candles_manager(
    context, symbol: str, time_frame: str, max_history: bool = False
) -> exchange_data.CandlesManager:
    if max_history and context.exchange_manager.is_backtesting:
        return await _load_backtesting_candles_manager(
            context.exchange_manager,
            symbol,
            time_frame,
        )
    return trading_api.get_symbol_candles_manager(
        trading_api.get_symbol_data(
            context.exchange_manager, symbol, allow_creation=False
        ),
        time_frame,
    )
