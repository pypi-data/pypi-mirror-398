from __future__ import annotations

from typing import NotRequired, TypedDict


class KeepKwargs(TypedDict):
    keep_last: NotRequired[int]
    keep_hourly: NotRequired[int]
    keep_daily: NotRequired[int]
    keep_weekly: NotRequired[int]
    keep_monthly: NotRequired[int]
    keep_yearly: NotRequired[int]
    keep_within: NotRequired[str]
    keep_within_hourly: NotRequired[str]
    keep_within_daily: NotRequired[str]
    keep_within_weekly: NotRequired[str]
    keep_within_monthly: NotRequired[str]
    keep_within_yearly: NotRequired[str]


DEFAULT_KEEP_KWARGS = KeepKwargs(
    keep_last=100,
    keep_hourly=24 * 7,
    keep_daily=30,
    keep_weekly=52,
    keep_monthly=5 * 12,
    keep_yearly=10,
    keep_within_hourly="7d",
    keep_within_daily="1m",
    keep_within_weekly="1y",
    keep_within_monthly="5y",
    keep_within_yearly="10y",
)


__all__ = ["DEFAULT_KEEP_KWARGS", "KeepKwargs"]
