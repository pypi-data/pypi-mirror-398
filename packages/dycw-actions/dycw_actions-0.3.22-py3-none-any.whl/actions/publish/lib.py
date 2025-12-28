from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.tempfile import TemporaryDirectory
from utilities.text import strip_and_dedent

from actions import __version__
from actions.logging import LOGGER
from actions.publish.settings import PUBLISH_SETTINGS
from actions.utilities import log_run

if TYPE_CHECKING:
    from typed_settings import Secret


def publish_package(
    *,
    username: str | None = PUBLISH_SETTINGS.username,
    password: Secret[str] | None = PUBLISH_SETTINGS.password,
    publish_url: str | None = PUBLISH_SETTINGS.publish_url,
    trusted_publishing: bool = PUBLISH_SETTINGS.trusted_publishing,
    native_tls: bool = PUBLISH_SETTINGS.native_tls,
) -> None:
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
             - username           = %s
             - password           = %s
             - publish_url        = %s
             - trusted_publishing = %s
             - native_tls         = %s
        """),
        publish_package.__name__,
        __version__,
        username,
        password,
        publish_url,
        trusted_publishing,
        native_tls,
    )
    with TemporaryDirectory() as temp:
        log_run("uv", "build", "--out-dir", str(temp), "--wheel", "--clear")
        log_run(
            "uv",
            "publish",
            *([] if username is None else ["--username", username]),
            *([] if password is None else ["--password", password]),
            *([] if publish_url is None else ["--publish-url", publish_url]),
            *(["--trusted-publishing", "always"] if trusted_publishing else []),
            *(["--native-tls"] if native_tls else []),
            f"{temp}/*",
        )


__all__ = ["publish_package"]
