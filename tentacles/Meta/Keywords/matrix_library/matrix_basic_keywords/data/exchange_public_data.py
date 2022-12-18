from tentacles.Meta.Keywords.matrix_library.strategies_builder.key_words.user_inputs2 import (
    user_input2,
)
from tentacles.Meta.Keywords.matrix_library.strategies_builder.key_words.tools.utilities import (
    start_measure_time,
    end_measure_time,
)

import tentacles.Meta.Keywords.scripting_library.data.reading.exchange_public_data as exchange_public_data


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
    if source_name == "close":
        return await exchange_public_data.Close(
            maker.ctx, symbol=symbol, time_frame=time_frame, max_history=max_history
        )
    if source_name == "open":
        return await exchange_public_data.Open(
            maker.ctx, symbol=symbol, time_frame=time_frame, max_history=max_history
        )
    if source_name == "high":
        return await exchange_public_data.High(
            maker.ctx, symbol=symbol, time_frame=time_frame, max_history=max_history
        )
    if source_name == "low":
        return await exchange_public_data.Low(
            maker.ctx, symbol=symbol, time_frame=time_frame, max_history=max_history
        )
    if source_name == "volume":
        return await exchange_public_data.Volume(
            maker.ctx, symbol=symbol, time_frame=time_frame, max_history=max_history
        )
    if source_name == "time":
        return await exchange_public_data.Time(
            maker.ctx, symbol=symbol, time_frame=time_frame, max_history=max_history
        )
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
