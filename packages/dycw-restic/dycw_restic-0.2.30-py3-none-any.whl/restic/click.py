from __future__ import annotations

from typing import TYPE_CHECKING, assert_never, override

from click import Context, Parameter, ParamType

from restic.repo import (
    SFTP,
    Backblaze,
    BackblazeMissingCredentialsError,
    Local,
    parse_repo,
)

if TYPE_CHECKING:
    import restic.repo


class Repo(ParamType):
    name = "repo"

    @override
    def __repr__(self) -> str:
        return self.name.upper()

    @override
    def convert(
        self,
        value: restic.repo.Repo | str,
        param: Parameter | None,
        ctx: Context | None,
    ) -> restic.repo.Repo:
        match value:
            case Backblaze() | Local() | SFTP():
                return value
            case str():
                try:
                    return parse_repo(value)
                except BackblazeMissingCredentialsError as error:
                    (msg,) = error.args
                    return self.fail(msg, param, ctx)
            case never:
                assert_never(never)


__all__ = ["Repo"]
