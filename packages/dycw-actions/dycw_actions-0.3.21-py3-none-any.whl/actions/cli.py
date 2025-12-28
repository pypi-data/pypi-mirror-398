from __future__ import annotations

from click import group
from utilities.click import CONTEXT_SETTINGS

from actions.hooks.cli import hooks_sub_cmd
from actions.publish.cli import publish_sub_cmd
from actions.requirements.cli import requirements_sub_cmd
from actions.sleep.cli import sleep_sub_cmd
from actions.tag.cli import tag_sub_cmd


@group(**CONTEXT_SETTINGS)
def _main() -> None: ...


_ = _main.command(name="hooks", **CONTEXT_SETTINGS)(hooks_sub_cmd)
_ = _main.command(name="publish", **CONTEXT_SETTINGS)(publish_sub_cmd)
_ = _main.command(name="requirements", **CONTEXT_SETTINGS)(requirements_sub_cmd)
_ = _main.command(name="sleep", **CONTEXT_SETTINGS)(sleep_sub_cmd)
_ = _main.command(name="tag", **CONTEXT_SETTINGS)(tag_sub_cmd)


if __name__ == "__main__":
    _main()
