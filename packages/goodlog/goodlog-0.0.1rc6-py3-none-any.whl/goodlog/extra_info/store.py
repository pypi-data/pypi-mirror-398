import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def set_info(**kwargs: Any) -> None:
    _ExtraLoggingInfo(**kwargs)


def get_info() -> dict[str, Any]:
    return _ExtraLoggingInfo().as_dict()


class _Singleton(type):
    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class _ExtraLoggingInfo(metaclass=_Singleton):
    def __init__(self, **kwargs: Any) -> None:
        self._info = kwargs.copy() if kwargs else dict()
        self._more_info: dict[str, Any] = dict()
        self._validate_serialization(self._info)

    def as_dict(self) -> dict[str, Any]:
        return {**self._info, **self._more_info}

    def add_more_info(self, **kwargs: Any) -> None:
        """
        Add more info in a temporary manner - it may be removed by calling the
        `remove_more_info` method.
        """
        self._validate_serialization(kwargs)
        self._more_info.update(**kwargs)

    def remove_more_info(self) -> dict[str, Any]:
        """
        Remove info that weren't provided in initialization but added later.
        """
        removed_info, self._more_info = self._more_info, dict()
        return removed_info

    @classmethod
    def _validate_serialization(cls, d: dict[str, Any]) -> None:
        try:
            json.dumps(d)
        except TypeError as e:
            raise ValueError(
                "The provided dict is not JSON-serializable"
            ) from e
