from __future__ import annotations

from typed_settings import Secret
from utilities.types import PathLike

type PasswordLike = Secret[str] | PathLike
type SecretLike = Secret[str] | str

__all__ = ["PasswordLike", "SecretLike"]
