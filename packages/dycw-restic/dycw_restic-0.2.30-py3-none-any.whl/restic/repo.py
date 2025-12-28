from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from re import search
from typing import TYPE_CHECKING, Self, assert_never, override

from typed_settings import Secret, load_settings
from utilities.os import temp_environ
from utilities.re import (
    ExtractGroupError,
    ExtractGroupsError,
    extract_group,
    extract_groups,
)

from restic.settings import LOADERS, SETTINGS, Settings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from restic.types import SecretLike


type Repo = Backblaze | Local | SFTP


@dataclass(order=True, slots=True)
class Backblaze:
    key_id: Secret[str]
    application_key: Secret[str]
    bucket: str
    path: Path

    @override
    def __eq__(self, other: object, /) -> bool:
        return (
            isinstance(other, type(self))
            and (self.key_id.get_secret_value() == other.key_id.get_secret_value())
            and (
                self.application_key.get_secret_value()
                == other.application_key.get_secret_value()
            )
            and (self.bucket == other.bucket)
            and (self.path == other.path)
        )

    @override
    def __hash__(self) -> int:
        return hash((
            self.key_id.get_secret_value(),
            self.application_key.get_secret_value(),
            self.bucket,
            self.path,
        ))

    @classmethod
    def parse(
        cls,
        text: str,
        /,
        *,
        key_id: SecretLike | None = SETTINGS.backblaze_key_id,
        application_key: SecretLike | None = SETTINGS.backblaze_application_key,
    ) -> Self:
        settings = load_settings(Settings, LOADERS)
        match key_id, settings.backblaze_key_id:
            case Secret() as key_id_use, _:
                ...
            case str(), _:
                key_id_use = Secret(key_id)
            case None, Secret() as key_id_use:
                ...
            case None, None:
                msg = "'BACKBLAZE_KEY_ID' is missing"
                raise ValueError(msg)
            case never:
                assert_never(never)
        match application_key, settings.backblaze_application_key:
            case Secret() as application_key_use, _:
                ...
            case str(), _:
                application_key_use = Secret(application_key)
            case None, Secret() as application_key_use:
                ...
            case None, None:
                msg = "'BACKBLAZE_APPLICATION_KEY' is missing"
                raise ValueError(msg)
            case never:
                assert_never(never)
        bucket, path = extract_groups(r"^b2:([^@:]+):([^@+]+)$", text)
        return cls(key_id_use, application_key_use, bucket, Path(path))

    @property
    def repository(self) -> str:
        return f"b2:{self.bucket}:{self.path}"


@dataclass(order=True, unsafe_hash=True, slots=True)
class Local:
    path: Path

    @classmethod
    def parse(cls, text: str, /) -> Self:
        path = extract_group(r"^local:([^@:]+)$", text)
        return cls(Path(path))

    @property
    def repository(self) -> str:
        return f"local:{self.path}"


@dataclass(order=True, unsafe_hash=True, slots=True)
class SFTP:
    user: str
    hostname: str
    path: Path

    @classmethod
    def parse(cls, text: str, /) -> Self:
        user, hostname, path = extract_groups(
            r"^sftp:([^@:]+)@([^@:]+):([^@:]+)$", text
        )
        return cls(user, hostname, Path(path))

    @property
    def repository(self) -> str:
        return f"sftp:{self.user}@{self.hostname}:{self.path}"


def parse_repo(text: str, /) -> Repo:
    try:
        return Backblaze.parse(text)
    except ValueError, ExtractGroupsError:
        if search("b2", text):
            msg = f"For a Backblaze repository {text!r}, the environment varaibles 'BACKBLAZE_KEY_ID' and 'BACKBLAZE_APPLICATION_KEY' must be defined"
            raise BackblazeMissingCredentialsError(msg) from None
    with suppress(ExtractGroupsError):
        return SFTP.parse(text)
    try:
        return Local.parse(text)
    except ExtractGroupError:
        return Local(Path(text))


class BackblazeMissingCredentialsError(Exception): ...


@contextmanager
def yield_repo_env(
    repo: Repo, /, *, env_var: str = "RESTIC_REPOSITORY"
) -> Iterator[None]:
    match repo:
        case Backblaze():
            with temp_environ(
                {env_var: repo.repository},
                B2_ACCOUNT_ID=repo.key_id.get_secret_value(),
                B2_ACCOUNT_KEY=repo.application_key.get_secret_value(),
            ):
                yield
        case Local() | SFTP():
            with temp_environ({env_var: repo.repository}):
                yield
        case never:
            assert_never(never)


__all__ = [
    "SFTP",
    "Backblaze",
    "BackblazeMissingCredentialsError",
    "Local",
    "Repo",
    "parse_repo",
    "yield_repo_env",
]
