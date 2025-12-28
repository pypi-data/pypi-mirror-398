from __future__ import annotations

from os import getenv
from typing import Any

from attrs import fields_dict
from typed_settings import (
    EnvLoader,
    FileLoader,
    Secret,
    TomlFormat,
    find,
    load_settings,
    option,
    secret,
    settings,
)
from utilities.os import CPU_COUNT

from restic.logging import LOGGER

CONFIG_FILE = getenv("RESTIC_CONFIG_FILE", "config.toml")
SECRETS_FILE = getenv("RESTIC_SECRETS_FILE", "secrets.toml")
LOADERS = [
    FileLoader({"*.toml": TomlFormat(None)}, [find(CONFIG_FILE), find(SECRETS_FILE)]),
    EnvLoader(""),
]


@settings(kw_only=True)
class Settings:
    # global
    dry_run: bool = option(default=False, help="Just print what would have been done")
    password: Secret[str] = secret(
        default=Secret("password"), help="Repository password or password file"
    )
    # backblaze
    backblaze_key_id: Secret[str] | None = secret(default=None, help="Backblaze key ID")
    backblaze_application_key: Secret[str] | None = secret(
        default=None, help="Backblaze application key"
    )
    # backup
    chmod: bool = option(default=False, help="Change permissions of the directory/file")
    chown: str | None = option(
        default=None, help="Change ownership of the directory/file"
    )
    exclude_backup: list[str] | None = option(default=None, help="Exclude a pattern")
    exclude_i_backup: list[str] | None = option(
        default=None, help="Exclude a pattern but ignores the casing of filenames"
    )
    read_concurrency: int = option(
        default=max(round(CPU_COUNT / 2), 2), help="Read `n` files concurrency"
    )
    tag_backup: list[str] | None = option(
        default=None, help="Add tags for the snapshot in the format `tag[,tag,...]`"
    )
    run_forget: bool = option(
        default=True, help="Automatically run the 'forget' command"
    )
    sleep: int | None = option(default=None, help="Sleep after a successful backup")
    # copy
    tag_copy: list[str] | None = option(
        default=None, help="Only consider snapshots including `tag[,tag,...]`"
    )
    # forget
    keep_last: int | None = option(default=None, help="Keep the last n snapshots")
    keep_hourly: int | None = option(
        default=None, help="Keep the last n hourly snapshots"
    )
    keep_daily: int | None = option(
        default=None, help="Keep the last n daily snapshots"
    )
    keep_weekly: int | None = option(
        default=None, help="Keep the last n weekly snapshots"
    )
    keep_monthly: int | None = option(
        default=None, help="Keep the last n monthly snapshots"
    )
    keep_yearly: int | None = option(
        default=None, help="Keep the last n yearly snapshots"
    )
    keep_within: str | None = option(
        default=None,
        help="Keep snapshots that are newer than duration relative to the latest snapshot",
    )
    keep_within_hourly: str | None = option(
        default=None,
        help="Keep hourly snapshots that are newer than duration relative to the latest snapshot",
    )
    keep_within_daily: str | None = option(
        default=None,
        help="Keep daily snapshots that are newer than duration relative to the latest snapshot",
    )
    keep_within_weekly: str | None = option(
        default=None,
        help="Keep weekly snapshots that are newer than duration relative to the latest snapshot",
    )
    keep_within_monthly: str | None = option(
        default=None,
        help="Keep monthly snapshots that are newer than duration relative to the latest snapshot",
    )
    keep_within_yearly: str | None = option(
        default=None,
        help="Keep yearly snapshots that are newer than duration relative to the latest snapshot",
    )
    prune: bool = option(
        default=True,
        help="Automatically run the 'prune' command if snapshots have been removed",
    )
    repack_cacheable_only: bool = option(
        default=False, help="Only repack packs which are cacheable"
    )
    repack_small: bool = option(
        default=True, help="Repack pack files below 80% of target pack size"
    )
    repack_uncompressed: bool = option(
        default=True, help="Repack all uncompressed data"
    )
    tag_forget: list[str] | None = option(
        default=None, help="Only consider snapshots including tag[,tag,...]"
    )
    # restore
    delete: bool = option(
        default=False,
        help="Delete files from target directory if they do not exist in snapshot",
    )
    exclude_restore: list[str] | None = option(default=None, help="Exclude a pattern")
    exclude_i_restore: list[str] | None = option(
        default=None, help="Exclude a pattern but ignores the casing of filenames"
    )
    include_restore: list[str] | None = option(default=None, help="Include a pattern")
    include_i_restore: list[str] | None = option(
        default=None, help="Include a pattern but ignores the casing of filenames"
    )
    tag_restore: list[str] | None = option(
        default=None,
        help='Only consider snapshots including tag[,tag,...], when snapshot ID "latest" is given',
    )
    snapshot: str = option(default="latest", help="Snapshot ID to restore")


LOGGER.info("Loading settings from '%s' and '%s'...", CONFIG_FILE, SECRETS_FILE)
SETTINGS = load_settings(Settings, LOADERS)


def _get_help(member_descriptor: Any, /) -> None:
    return fields_dict(Settings)[member_descriptor.__name__].metadata["typed-settings"][
        "help"
    ]


@settings(kw_only=True)
class InitSettings:
    password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )


@settings(kw_only=True)
class BackupSettings:
    chmod: bool = option(default=SETTINGS.chmod, help=_get_help(Settings.chmod))
    chown: str | None = option(default=SETTINGS.chown, help=_get_help(Settings.chown))
    password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )
    dry_run: bool = option(default=SETTINGS.dry_run, help=_get_help(Settings.dry_run))
    exclude: list[str] | None = option(
        default=SETTINGS.exclude_backup, help=_get_help(Settings.exclude_backup)
    )
    exclude_i: list[str] | None = option(
        default=SETTINGS.exclude_i_backup, help=_get_help(Settings.exclude_i_backup)
    )
    read_concurrency: int = option(
        default=SETTINGS.read_concurrency, help=_get_help(Settings.read_concurrency)
    )
    tag_backup: list[str] | None = option(
        default=SETTINGS.tag_backup, help=_get_help(Settings.tag_backup)
    )
    run_forget: bool = option(
        default=SETTINGS.run_forget, help=_get_help(Settings.run_forget)
    )
    keep_last: int | None = option(
        default=SETTINGS.keep_last, help=_get_help(Settings.keep_last)
    )
    keep_hourly: int | None = option(
        default=SETTINGS.keep_hourly, help=_get_help(Settings.keep_hourly)
    )
    keep_daily: int | None = option(
        default=SETTINGS.keep_daily, help=_get_help(Settings.keep_daily)
    )
    keep_weekly: int | None = option(
        default=SETTINGS.keep_weekly, help=_get_help(Settings.keep_weekly)
    )
    keep_monthly: int | None = option(
        default=SETTINGS.keep_monthly, help=_get_help(Settings.keep_monthly)
    )
    keep_yearly: int | None = option(
        default=SETTINGS.keep_yearly, help=_get_help(Settings.keep_yearly)
    )
    keep_within: str | None = option(
        default=SETTINGS.keep_within, help=_get_help(Settings.keep_within)
    )
    keep_within_hourly: str | None = option(
        default=SETTINGS.keep_within_hourly, help=_get_help(Settings.keep_within_hourly)
    )
    keep_within_daily: str | None = option(
        default=SETTINGS.keep_within_daily, help=_get_help(Settings.keep_within_daily)
    )
    keep_within_weekly: str | None = option(
        default=SETTINGS.keep_within_weekly, help=_get_help(Settings.keep_within_weekly)
    )
    keep_within_monthly: str | None = option(
        default=SETTINGS.keep_within_monthly,
        help=_get_help(Settings.keep_within_monthly),
    )
    keep_within_yearly: str | None = option(
        default=SETTINGS.keep_within_yearly, help=_get_help(Settings.keep_within_yearly)
    )
    prune: bool = option(default=SETTINGS.prune, help=_get_help(Settings.prune))
    repack_cacheable_only: bool = option(
        default=SETTINGS.repack_cacheable_only,
        help=_get_help(Settings.repack_cacheable_only),
    )
    repack_small: bool = option(
        default=SETTINGS.repack_small, help=_get_help(Settings.repack_small)
    )
    repack_uncompressed: bool = option(
        default=SETTINGS.repack_uncompressed,
        help=_get_help(Settings.repack_uncompressed),
    )
    tag_forget: list[str] | None = option(
        default=SETTINGS.tag_forget, help=_get_help(Settings.tag_forget)
    )
    sleep: int | None = option(default=SETTINGS.sleep, help=_get_help(Settings.sleep))


@settings(kw_only=True)
class CopySettings:
    src_password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )
    dest_password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )
    tag: list[str] | None = option(
        default=SETTINGS.tag_copy, help=_get_help(Settings.tag_copy)
    )
    sleep: int | None = option(default=SETTINGS.sleep, help=_get_help(Settings.sleep))


@settings(kw_only=True)
class ForgetSettings:
    password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )
    dry_run: bool = option(default=SETTINGS.dry_run, help=_get_help(Settings.dry_run))
    keep_last: int | None = option(
        default=SETTINGS.keep_last, help=_get_help(Settings.keep_last)
    )
    keep_hourly: int | None = option(
        default=SETTINGS.keep_hourly, help=_get_help(Settings.keep_hourly)
    )
    keep_daily: int | None = option(
        default=SETTINGS.keep_daily, help=_get_help(Settings.keep_daily)
    )
    keep_weekly: int | None = option(
        default=SETTINGS.keep_weekly, help=_get_help(Settings.keep_weekly)
    )
    keep_monthly: int | None = option(
        default=SETTINGS.keep_monthly, help=_get_help(Settings.keep_monthly)
    )
    keep_yearly: int | None = option(
        default=SETTINGS.keep_yearly, help=_get_help(Settings.keep_yearly)
    )
    keep_within: str | None = option(
        default=SETTINGS.keep_within, help=_get_help(Settings.keep_within)
    )
    keep_within_hourly: str | None = option(
        default=SETTINGS.keep_within_hourly, help=_get_help(Settings.keep_within_hourly)
    )
    keep_within_daily: str | None = option(
        default=SETTINGS.keep_within_daily, help=_get_help(Settings.keep_within_daily)
    )
    keep_within_weekly: str | None = option(
        default=SETTINGS.keep_within_weekly, help=_get_help(Settings.keep_within_weekly)
    )
    keep_within_monthly: str | None = option(
        default=SETTINGS.keep_within_monthly,
        help=_get_help(Settings.keep_within_monthly),
    )
    keep_within_yearly: str | None = option(
        default=SETTINGS.keep_within_yearly, help=_get_help(Settings.keep_within_yearly)
    )
    prune: bool = option(default=SETTINGS.prune, help=_get_help(Settings.prune))
    repack_cacheable_only: bool = option(
        default=SETTINGS.repack_cacheable_only,
        help=_get_help(Settings.repack_cacheable_only),
    )
    repack_small: bool = option(
        default=SETTINGS.repack_small, help=_get_help(Settings.repack_small)
    )
    repack_uncompressed: bool = option(
        default=SETTINGS.repack_uncompressed,
        help=_get_help(Settings.repack_uncompressed),
    )
    tag: list[str] | None = option(
        default=SETTINGS.tag_forget, help=_get_help(Settings.tag_forget)
    )


@settings(kw_only=True)
class RestoreSettings:
    password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )
    delete: bool = option(default=SETTINGS.delete, help=_get_help(Settings.delete))
    dry_run: bool = option(default=SETTINGS.dry_run, help=_get_help(Settings.dry_run))
    exclude: list[str] | None = option(
        default=SETTINGS.exclude_restore, help=_get_help(Settings.exclude_restore)
    )
    exclude_i: list[str] | None = option(
        default=SETTINGS.exclude_i_restore, help=_get_help(Settings.exclude_i_restore)
    )
    include: list[str] | None = option(
        default=SETTINGS.include_restore, help=_get_help(Settings.include_restore)
    )
    include_i: list[str] | None = option(
        default=SETTINGS.include_i_restore, help=_get_help(Settings.include_i_restore)
    )
    tag: list[str] | None = option(
        default=SETTINGS.tag_restore, help=_get_help(Settings.tag_restore)
    )
    snapshot: str = option(default=SETTINGS.snapshot, help=_get_help(Settings.snapshot))


@settings(kw_only=True)
class SnapshotsSettings:
    password: Secret[str] = secret(
        default=SETTINGS.password, help=_get_help(Settings.password)
    )


__all__ = [
    "LOADERS",
    "SETTINGS",
    "BackupSettings",
    "CopySettings",
    "ForgetSettings",
    "InitSettings",
    "RestoreSettings",
    "Settings",
    "SnapshotsSettings",
]
