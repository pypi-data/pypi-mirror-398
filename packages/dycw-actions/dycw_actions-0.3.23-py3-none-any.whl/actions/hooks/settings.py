from __future__ import annotations

from typed_settings import load_settings, option, settings

from actions.utilities import LOADER, convert_list_strs


@settings
class HooksSettings:
    repos: list[str] | None = option(
        default=None,
        converter=convert_list_strs,
        help="The repos whose hooks are to be run",
    )
    hooks: list[str] | None = option(
        default=None, converter=convert_list_strs, help="The hooks to be run"
    )
    sleep: int = option(default=1, help="Sleep in between runs")


HOOKS_SETTINGS = load_settings(HooksSettings, [LOADER])


__all__ = ["HOOKS_SETTINGS", "HooksSettings"]
