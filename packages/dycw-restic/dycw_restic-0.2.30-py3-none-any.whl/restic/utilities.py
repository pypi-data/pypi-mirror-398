from __future__ import annotations

from contextlib import contextmanager
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Literal, assert_never

from typed_settings import Secret
from utilities.os import temp_environ
from utilities.subprocess import run
from utilities.tempfile import TemporaryFile

from restic.settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Iterator

    from utilities.types import PathLike

    from restic.types import PasswordLike


def expand_bool(flag: str, /, *, bool_: bool = False) -> list[str]:
    return [f"--{flag}"] if bool_ else []


def expand_dry_run(*, dry_run: bool = False) -> list[str]:
    return expand_bool("dry-run", bool_=dry_run)


def expand_exclude(*, exclude: list[str] | None = None) -> list[str]:
    return _expand_list("exclude", arg=exclude)


def expand_exclude_i(*, exclude_i: list[str] | None = None) -> list[str]:
    return _expand_list("iexclude", arg=exclude_i)


def expand_include(*, include: list[str] | None = None) -> list[str]:
    return _expand_list("include", arg=include)


def expand_include_i(*, include_i: list[str] | None = None) -> list[str]:
    return _expand_list("iinclude", arg=include_i)


def expand_keep(freq: str, /, *, n: int | None = None) -> list[str]:
    return [] if n is None else [f"--keep-{freq}", str(n)]


def expand_keep_within(freq: str, /, *, duration: str | None = None) -> list[str]:
    return [] if duration is None else [f"--keep-{freq}", duration]


def expand_tag(*, tag: list[str] | None = None) -> list[str]:
    return _expand_list("tag", arg=tag)


def run_chmod(path: PathLike, type_: Literal["f", "d"], mode: str, /) -> None:
    run("sudo", "find", str(path), "-type", type_, "-exec", "chmod", mode, "{}", "+")


@contextmanager
def yield_password(
    *, password: PasswordLike = SETTINGS.password, env_var: str = "RESTIC_PASSWORD_FILE"
) -> Iterator[None]:
    match password:
        case Secret():
            value = password.get_secret_value()
        case Path() | str() as value:
            ...
        case never:
            assert_never(never)
    match value:
        case Path():
            if value.is_file():
                with temp_environ({env_var: str(value)}):
                    yield
            else:
                msg = f"Password file not found: '{value!s}'"
                raise FileNotFoundError(msg)
        case str():
            if Path(value).is_file():
                with temp_environ({env_var: value}):
                    yield
            else:
                with TemporaryFile() as temp, temp_environ({env_var: str(temp)}):
                    _ = temp.write_text(value)
                    yield
        case never:
            assert_never(never)


def _expand_list(flag: str, /, *, arg: list[str] | None = None) -> list[str]:
    return (
        [] if arg is None else list(chain.from_iterable([f"--{flag}", a] for a in arg))
    )


__all__ = [
    "expand_bool",
    "expand_dry_run",
    "expand_exclude",
    "expand_exclude_i",
    "expand_include",
    "expand_include_i",
    "expand_keep",
    "expand_keep_within",
    "expand_tag",
    "run_chmod",
    "yield_password",
]
