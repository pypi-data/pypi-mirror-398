from __future__ import annotations

from rich.pretty import pretty_repr
from typed_settings import click_options
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

from actions import __version__
from actions.hooks.lib import run_hooks
from actions.hooks.settings import HooksSettings
from actions.logging import LOGGER
from actions.settings import CommonSettings
from actions.utilities import LOADER


@click_options(CommonSettings, [LOADER], show_envvars_in_help=True, argname="common")
@click_options(HooksSettings, [LOADER], show_envvars_in_help=True, argname="hooks")
def hooks_sub_cmd(*, common: CommonSettings, hooks: HooksSettings) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
            %s
            %s
        """),
        run_hooks.__name__,
        __version__,
        pretty_repr(common),
        pretty_repr(hooks),
    )
    run_hooks(repos=hooks.repos, hooks=hooks.hooks, sleep=hooks.sleep)


__all__ = ["hooks_sub_cmd"]
