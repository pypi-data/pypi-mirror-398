import functools
import json
import logging
from collections import OrderedDict
from typing import Any


class JSONFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        # fields to always include (always expected to exist)
        dict_record: dict[str, Any] = OrderedDict(
            logger_name=record.name,
            timestamp=self.formatTime(record),
            log_level=record.levelname,
            message=record.getMessage(),
        )

        # Fields to include only if they exist, with specific parsing
        if record.exc_info:
            dict_record["exception"] = self.formatException(record.exc_info)

        # Fields related to source code context
        code_context: dict[str, Any] = dict()
        for field, new_name in (
            ("funcName", "function_name"),
            ("pathname", "python_file_path"),
            ("lineno", "line_number"),
            ("module", "module_name"),
        ):
            value = getattr(record, field, None)
            if value is not None:
                code_context[new_name] = value
        dict_record["code_context"] = code_context

        # Fields to add with original name only if they exist with a value
        for field in ("exc_text", "extra_info", "stack_info"):
            value = getattr(record, field, None)
            if value is not None:
                dict_record[field] = value

        # Add any extra fields from LogRecord.__dict__
        # (like those passed via extra= parameter)
        exclude = set(dict_record.keys())
        exclude.update(_standard_log_record_attributes())
        for key, value in record.__dict__.items():
            if key not in exclude and value is not None:
                dict_record[key] = value

        return json.dumps(dict_record)


@functools.lru_cache
def _standard_log_record_attributes() -> set[str]:
    return set(
        logging.LogRecord(
            name="dummy", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        ).__dict__.keys()
    )
