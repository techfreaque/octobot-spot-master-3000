import time


def start_measure_time(message=None):
    if message:
        print(message + " started")
    return time.time()


def end_measure_time(m_time, message, min_duration=None):
    duration = round(time.time() - m_time, 2)
    if not min_duration or min_duration < duration:
        print(f"{message} done {duration}s")


def end_measure_live_time(ctx, m_time, message, min_duration=None):
    duration = round(time.time() - m_time, 2)
    if not min_duration or min_duration < duration:
        ctx.logger.info(f"{message} done {duration}s")
