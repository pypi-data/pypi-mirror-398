from __future__ import annotations

from typed_settings import load_settings, option, settings

from actions.utilities import LOADER


@settings
class SleepSettings:
    min: int = option(default=0, help="Minimum duration, in seconds")
    max: int = option(default=3600, help="Maximum duration, in seconds")
    step: int = option(default=1, help="Step duration, in seconds")
    log_freq: int = option(default=60, help="Log frequency, in seconds")


SLEEP_SETTINGS = load_settings(SleepSettings, [LOADER])


__all__ = ["SLEEP_SETTINGS", "SleepSettings"]
