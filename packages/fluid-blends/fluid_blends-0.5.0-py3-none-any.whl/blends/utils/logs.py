import logging
from asyncio import to_thread
from enum import Enum
from os import environ
from pathlib import Path
from types import TracebackType

import bugsnag

from blends.utils.bugs import META as BUGS_META
from blends.utils.env import is_fluid_batch_env

LoggeableObject = str | int | float | Enum | Path | BaseException | type[BaseException] | None

_LOGGER = logging.getLogger("Blends")


def log_blocking(
    level: str,
    msg: str,
    *args: LoggeableObject,
    **kwargs: dict[str, LoggeableObject],
) -> None:
    getattr(_LOGGER, level)(msg, *args, **kwargs)


async def log(
    level: str,
    msg: str,
    *args: LoggeableObject,
    **kwargs: dict[str, LoggeableObject],
) -> None:
    await to_thread(log_blocking, level, msg, *args, **kwargs)


def log_to_remote_blocking(
    *,
    msg: (
        str
        | Exception
        | tuple[type[BaseException] | None, BaseException | None, TracebackType | None]
    ),
    severity: str,  # info, error, warning
    **meta_data: str,
) -> None:
    if environ.get("CI_COMMIT_REF_NAME", "trunk") == "trunk":
        meta_data.update(BUGS_META)
        bugsnag.notify(
            Exception(msg) if isinstance(msg, str) else msg,  # type: ignore[arg-type]
            meta_data=dict(meta_data),
            severity=severity,
            unhandled=is_fluid_batch_env(),
        )


def log_to_remote_handled(
    *,
    msg: str,
    severity: str,
) -> None:
    if is_fluid_batch_env():
        bugsnag.notify(
            Exception(msg),
            meta_data=BUGS_META,
            severity=severity,
            unhandled=False,
        )
    elif environ.get("CI_COMMIT_REF_NAME", "trunk") != "trunk":
        log_blocking("error", msg)


async def log_to_remote(
    *,
    msg: (
        str
        | Exception
        | tuple[
            type[BaseException] | None,
            BaseException | None,
            TracebackType | None,
        ]
    ),
    severity: str,  # info, error, warning
    **meta_data: str,
) -> None:
    await to_thread(
        log_to_remote_blocking,
        msg=msg,
        severity=severity,
        **meta_data,
    )
