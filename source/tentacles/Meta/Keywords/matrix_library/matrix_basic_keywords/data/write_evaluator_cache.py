import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants
import tentacles.Meta.Keywords.scripting_library.data.reading.exchange_public_data as exchange_public_data
import numpy as np


async def store_evaluator_history(ctx, indicator_values, signals_data,
                                  plot_enabled=True, additional_values_by_key=None):
    # store it in one go
    times = await exchange_public_data.Time(ctx, max_history=True)
    data_length = len(signals_data)
    times = times[-data_length:]

    if plot_enabled:
        plot_cache_key = f"{commons_enums.CacheDatabaseColumns.VALUE.value}" \
                         f"{commons_constants.CACHE_RELATED_DATA_SEPARATOR}y"
        y_cache = []
        y_times = []
        indicator_values = indicator_values[-data_length:]
        for index, signal_value in enumerate(signals_data):
            if signal_value:
                y_cache.append(indicator_values[index])
                y_times.append(times[index])
        await ctx.set_cached_values(values=y_cache, cache_keys=y_times,
                                    value_key=plot_cache_key)
    await ctx.set_cached_values(values=signals_data, cache_keys=times,
                                value_key=commons_enums.CacheDatabaseColumns.VALUE.value,
                                additional_values_by_key=additional_values_by_key)
    # write cache flag on the first candle, cause we dont know on which timestamp the first cached result is
    await ctx.set_cached_value(value=True, value_key="csh")


async def store_indicator_history(ctx, indicator_values, value_key=commons_enums.CacheDatabaseColumns.VALUE.value,
                                  additional_values_by_key=None):
    if additional_values_by_key is None:
        additional_values_by_key = {}
    if max(indicator_values) < 1 and min(indicator_values) > -1:
        round_decimals = 8
    else:
        round_decimals = 3
    # store it in one go
    time_data = await exchange_public_data.Time(ctx, max_history=True)
    cut_t = time_data[-len(indicator_values):]
    if round_decimals:
        indicator_values = np.round(indicator_values, decimals=round_decimals)
        if additional_values_by_key:
            for key in additional_values_by_key:
                additional_values_by_key[key] = np.round(additional_values_by_key[key], decimals=2)
    await ctx.set_cached_values(values=indicator_values, cache_keys=cut_t,
                                value_key=value_key,
                                additional_values_by_key=additional_values_by_key)
    # write cache flag on the first candle, cause we dont know on which timestamp the first cached result is
    await ctx.set_cached_value(value=True, cache_key=time_data[0], value_key="csh")
