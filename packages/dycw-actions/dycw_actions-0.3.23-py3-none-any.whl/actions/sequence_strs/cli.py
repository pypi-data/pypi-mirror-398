from __future__ import annotations

from pathlib import Path

import click
from click import argument
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

from actions import __version__
from actions.logging import LOGGER
from actions.sequence_strs.lib import replace_sequence_strs


@argument(
    "paths",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
def sequence_strs_sub_cmd(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
             - paths = %s
        """),
        replace_sequence_strs.__name__,
        __version__,
        paths,
    )
    replace_sequence_strs(*paths)


__all__ = ["sequence_strs_sub_cmd"]
