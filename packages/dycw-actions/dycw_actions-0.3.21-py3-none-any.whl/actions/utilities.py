from __future__ import annotations

from typing import TYPE_CHECKING, Literal, assert_never, overload

from typed_settings import EnvLoader, Secret
from utilities.subprocess import run

from actions.logging import LOGGER

if TYPE_CHECKING:
    from utilities.types import StrStrMapping

    from actions.types import SecretLike


LOADER = EnvLoader("")


def convert_list_strs(
    x: str | list[str] | tuple[str, ...] | None, /
) -> list[str] | None:
    match x:
        case None:
            return None
        case list():
            return x
        case tuple():
            return None if x == () else list(x)
        case str():
            return x.splitlines()
        case never:
            assert_never(never)


def convert_secret_str(x: SecretLike | None, /) -> Secret[str] | None:
    empty = {None, ""}
    match x:
        case Secret():
            return None if x.get_secret_value() in empty else x
        case str():
            return None if x in empty else Secret(x)
        case None:
            return None
        case never:
            assert_never(never)


def convert_str(x: str | None, /) -> str | None:
    match x:
        case str():
            return None if x == "" else x
        case None:
            return None
        case never:
            assert_never(never)


@overload
def log_run(
    cmd: SecretLike,
    /,
    *cmds: SecretLike,
    env: StrStrMapping | None = None,
    print: bool = False,
    return_: Literal[True],
) -> str: ...
@overload
def log_run(
    cmd: SecretLike,
    /,
    *cmds: SecretLike,
    env: StrStrMapping | None = None,
    print: bool = False,
    return_: Literal[False] = False,
) -> None: ...
@overload
def log_run(
    cmd: SecretLike,
    /,
    *cmds: SecretLike,
    env: StrStrMapping | None = None,
    print: bool = False,
    return_: bool = False,
) -> str | None: ...
def log_run(
    cmd: SecretLike,
    /,
    *cmds: SecretLike,
    env: StrStrMapping | None = None,
    print: bool = False,  # noqa: A002
    return_: bool = False,
) -> str | None:
    all_cmds = [cmd, *cmds]
    LOGGER.info("Running '%s'...", " ".join(map(str, all_cmds)))
    unwrapped = [c if isinstance(c, str) else c.get_secret_value() for c in all_cmds]
    return run(*unwrapped, env=env, print=print, return_=return_, logger=LOGGER)


__all__ = [
    "LOADER",
    "convert_list_strs",
    "convert_secret_str",
    "convert_str",
    "log_run",
]
