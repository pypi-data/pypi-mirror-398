from __future__ import annotations

from typed_settings import EnvLoader, load_settings, option, settings
from utilities.getpass import USER

LOADER = EnvLoader("")


@settings
class Settings:
    name: str = option(default="name", help="Cron job name")
    prepend_path: list[str] | None = option(default=None, help="Paths to prepend")
    schedule: str = option(default="* * * * *", help="Cron job schedule")
    user: str = option(default=USER, help="Cron job user")
    timeout: int = option(default=60, help="Seconds until timing-out the cron job")
    kill_after: int = option(
        default=10, help="Seconds until killing the cron job (after timeout)"
    )
    command: str = option(default="true", help="Command or executable script")
    args: list[str] | None = option(default=None, help="Command arguments")
    logs_keep: int = option(default=7, help="Number of logs to keep")


SETTINGS = load_settings(Settings, [LOADER])


__all__ = ["LOADER", "SETTINGS", "Settings"]
