from __future__ import annotations

from pathlib import Path

import click
from click import argument
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

from actions import __version__
from actions.logging import LOGGER
from actions.requirements.lib import format_requirements
from actions.sleep.lib import random_sleep


@argument(
    "paths",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
def requirements_sub_cmd(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
             - paths = %s
        """),
        random_sleep.__name__,
        __version__,
        paths,
    )
    format_requirements(*paths)


__all__ = ["requirements_sub_cmd"]
