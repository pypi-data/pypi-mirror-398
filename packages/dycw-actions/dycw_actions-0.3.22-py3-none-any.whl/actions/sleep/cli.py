from __future__ import annotations

from rich.pretty import pretty_repr
from typed_settings import click_options
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

from actions import __version__
from actions.logging import LOGGER
from actions.settings import CommonSettings
from actions.sleep.lib import random_sleep
from actions.sleep.settings import SleepSettings
from actions.utilities import LOADER


@click_options(CommonSettings, [LOADER], show_envvars_in_help=True, argname="common")
@click_options(SleepSettings, [LOADER], show_envvars_in_help=True, argname="sleep")
def sleep_sub_cmd(*, common: CommonSettings, sleep: SleepSettings) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
            %s
            %s
        """),
        random_sleep.__name__,
        __version__,
        pretty_repr(common),
        pretty_repr(sleep),
    )
    random_sleep(
        min_=sleep.min, max_=sleep.max, step=sleep.step, log_freq=sleep.log_freq
    )


__all__ = ["sleep_sub_cmd"]
