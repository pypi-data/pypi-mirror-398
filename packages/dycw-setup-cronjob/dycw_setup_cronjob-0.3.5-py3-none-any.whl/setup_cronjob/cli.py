from __future__ import annotations

from click import command
from rich.pretty import pretty_repr
from typed_settings import click_options
from utilities.click import CONTEXT_SETTINGS
from utilities.logging import basic_config
from utilities.os import is_pytest

from setup_cronjob.lib import setup_cronjob
from setup_cronjob.logging import LOGGER
from setup_cronjob.settings import LOADER, Settings


@command(**CONTEXT_SETTINGS)
@click_options(Settings, [LOADER], show_envvars_in_help=True)
def _main(settings: Settings, /) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    LOGGER.info("Settings = %s", pretty_repr(settings))
    setup_cronjob(
        name=settings.name,
        prepend_path=settings.prepend_path,
        schedule=settings.schedule,
        user=settings.user,
        timeout=settings.timeout,
        kill_after=settings.kill_after,
        command=settings.command,
        args=settings.args,
        logs_keep=settings.logs_keep,
    )


if __name__ == "__main__":
    _main()
