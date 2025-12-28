from __future__ import annotations

from math import ceil, floor
from random import choice
from time import sleep

from utilities.text import strip_and_dedent
from utilities.whenever import get_now
from whenever import TimeDelta, ZonedDateTime

from actions import __version__
from actions.logging import LOGGER
from actions.sleep.settings import SLEEP_SETTINGS


def random_sleep(
    *,
    min_: int = SLEEP_SETTINGS.min,
    max_: int = SLEEP_SETTINGS.max,
    step: int = SLEEP_SETTINGS.step,
    log_freq: int = SLEEP_SETTINGS.log_freq,
) -> None:
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
             - min_     = %s
             - max_     = %s
             - step     = %s
             - log_freq = %s
        """),
        random_sleep.__name__,
        __version__,
        min_,
        max_,
        step,
        log_freq,
    )
    start = get_now()
    delta = TimeDelta(seconds=choice(range(min_, max_, step)))
    LOGGER.info("Sleeping for %s...", delta)
    end = (start + delta).round(mode="ceil")
    while (now := get_now()) < end:
        _intermediate(start, now, end, log_freq=log_freq)
    LOGGER.info("Finished sleeping for %s", delta)


def _intermediate(
    start: ZonedDateTime,
    now: ZonedDateTime,
    end: ZonedDateTime,
    /,
    *,
    log_freq: int = SLEEP_SETTINGS.log_freq,
) -> None:
    elapsed = TimeDelta(seconds=floor((now - start).in_seconds()))
    remaining = TimeDelta(seconds=ceil((end - now).in_seconds()))
    this_sleep = min(remaining, TimeDelta(seconds=log_freq))
    LOGGER.info(
        "Sleeping for %s... (elapsed = %s, remaining = %s)",
        this_sleep,
        elapsed,
        remaining,
    )
    sleep(round(this_sleep.in_seconds()))


__all__ = ["random_sleep"]
