from logging.config import dictConfig
from typing import Any

from .extra_info.store import set_info


def configure_logging(
    global_extra_info: dict[str, Any] | None = None,
) -> None:
    if global_extra_info is None:
        global_extra_info = {}
    set_info(**global_extra_info)
    dictConfig(
        config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json_formatter": {
                    "()": "goodlog.formats.JSONFormatter",
                }
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "json_formatter",
                    "filters": ["context"],
                }
            },
            "filters": {
                "context": {
                    "()": "goodlog.filters.AddExtraInfoFilter"
                },
            },
            "root": {
                "handlers": ["stdout"],
                "level": "INFO",
            },
        }
    )
