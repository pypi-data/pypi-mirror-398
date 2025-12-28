from __future__ import annotations

from typed_settings import Secret, load_settings, option, secret, settings

from actions.utilities import LOADER, convert_secret_str, convert_str


@settings
class PublishSettings:
    username: str | None = option(
        default=None, converter=convert_str, help="The username of the upload"
    )
    password: Secret[str] | None = secret(
        default=None, converter=convert_secret_str, help="The password for the upload"
    )
    publish_url: str | None = option(
        default=None, converter=convert_str, help="The URL of the upload endpoint"
    )
    trusted_publishing: bool = option(
        default=False, help="Configure trusted publishing"
    )
    native_tls: bool = option(
        default=False,
        help="Whether to load TLS certificates from the platform's native certificate store",
    )


PUBLISH_SETTINGS = load_settings(PublishSettings, [LOADER])


__all__ = ["PUBLISH_SETTINGS", "PublishSettings"]
