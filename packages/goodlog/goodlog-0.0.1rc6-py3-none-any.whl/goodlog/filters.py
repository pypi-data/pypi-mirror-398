import logging

import goodlog.extra_info.store


class AddExtraInfoFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        setattr(record, "extra_info", goodlog.extra_info.store.get_info())
        return True
