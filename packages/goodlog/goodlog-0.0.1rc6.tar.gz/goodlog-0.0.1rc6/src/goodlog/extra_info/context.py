import contextlib
import typing
from typing import Any

from goodlog.extra_info.store import _ExtraLoggingInfo


@contextlib.contextmanager
def ephemeral_info_context(
        **extra_info: Any,
) -> typing.Generator[None, None, None]:
    add(**extra_info)
    try:
        yield
    finally:
        remove()


def add(**kwargs: Any) -> None:
    _ExtraLoggingInfo().add_more_info(**kwargs)


def remove() -> dict[str, Any]:
    return _ExtraLoggingInfo().remove_more_info()
