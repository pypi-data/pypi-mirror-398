from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, cast

from utilities.platform import SYSTEM
from utilities.subprocess import run
from utilities.tempfile import TemporaryFile

from setup_cronjob.logging import LOGGER
from setup_cronjob.settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from utilities.types import PathLike


_PACKAGE_ROOT = cast("Path", files("setup_cronjob"))


def setup_cronjob(
    *,
    name: str = SETTINGS.name,
    prepend_path: Sequence[PathLike] | None = SETTINGS.prepend_path,
    schedule: str = SETTINGS.schedule,
    user: str = SETTINGS.user,
    timeout: int = SETTINGS.timeout,
    kill_after: int = SETTINGS.kill_after,
    command: PathLike = SETTINGS.command,
    args: list[str] | None = SETTINGS.args,
    logs_keep: int = SETTINGS.logs_keep,
) -> None:
    """Set up a cronjob & logrotate."""
    if SYSTEM != "linux":
        msg = f"System must be 'linux'; got {SYSTEM!r}"
        raise TypeError(msg)
    _write_file(
        f"/etc/cron.d/{name}",
        _get_crontab(
            prepend_path=prepend_path,
            schedule=schedule,
            user=user,
            name=name,
            timeout=timeout,
            kill_after=kill_after,
            command=command,
            args=args,
        ),
    )
    _write_file(
        f"/etc/logrotate.d/{name}", _get_logrotate(name=name, logs_keep=logs_keep)
    )


def _get_crontab(
    *,
    prepend_path: Sequence[PathLike] | None = SETTINGS.prepend_path,
    schedule: str = SETTINGS.schedule,
    user: str = SETTINGS.user,
    name: str = SETTINGS.name,
    timeout: int = SETTINGS.timeout,
    kill_after: int = SETTINGS.kill_after,
    command: PathLike | None = SETTINGS.command,
    args: list[str] | None = SETTINGS.args,
) -> str:
    return Template((_PACKAGE_ROOT / "cron.tmpl").read_text()).substitute(
        PREPEND_PATH=""
        if prepend_path is None
        else "".join(f"{p}:" for p in prepend_path),
        SCHEDULE=schedule,
        USER=user,
        NAME=name,
        TIMEOUT=timeout,
        KILL_AFTER=kill_after,
        COMMAND=command,
        SPACE=" " if (args is not None) and (len(args) >= 1) else "",
        ARGS="" if args is None else " ".join(args),
    )


def _get_logrotate(
    *, name: str = SETTINGS.name, logs_keep: int = SETTINGS.logs_keep
) -> str:
    return Template((_PACKAGE_ROOT / "logrotate.tmpl").read_text()).substitute(
        NAME=name, ROTATE=logs_keep
    )


def _write_file(path: PathLike, text: str, /) -> None:
    LOGGER.info("Writing '%s'...", path)
    with TemporaryFile() as src:
        _ = src.write_text(text)
        run("sudo", "mv", str(src), str(path))
    run("sudo", "chown", "root:root", str(path))
    run("sudo", "chmod", "u=rw,g=r,o=r", str(path))


__all__ = ["setup_cronjob"]
