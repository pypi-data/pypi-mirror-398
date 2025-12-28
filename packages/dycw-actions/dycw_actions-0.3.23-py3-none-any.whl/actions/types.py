from __future__ import annotations

from typed_settings import Secret

type SecretLike = str | Secret[str]


__all__ = ["SecretLike"]
