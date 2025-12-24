import logging
from typing import Any, Optional, cast


class LogRecordParser:
    _global_instance: Optional["LogRecordParser"] = None

    def __init__(self):
        # Standard LogRecord fields that should not be considered extra
        self._standard_attrs = list(
            logging.LogRecord("", 0, "", 0, "", (), None, "").__dict__.keys()
        )
        self._standard_attrs.append("asctime")
        self._standard_attrs.append("message")
        # The state field is add via LoggingStorageLoggingFilter
        # and we handle that separately
        self._standard_attrs.append("state")

    def parse_extra_info(self, log_record: logging.LogRecord) -> dict[str, Any]:
        """
        Parse extra data from the given log record that is not considered
        standard. That is, which is added at logging time. For example, for
        the log line:

        self._logger.info("My log message", extra={'user': user_id})

        This method will return {'user': user_id}
        """
        extra_info = {
            key: value
            for key, value in log_record.__dict__.items()
            if key not in self._standard_attrs
        }
        return extra_info

    def parse_state_info(self, log_record: logging.LogRecord) -> dict[str, Any]:
        """
        Parse state data from the given log record that is added via LoggingStorage.
        """
        if hasattr(log_record, "state") and isinstance(log_record.state, dict):
            return cast(dict[str, Any], log_record.state)

        return {}

    @classmethod
    def get_global(cls) -> "LogRecordParser":
        if cls._global_instance is None:
            raise RuntimeError("LogRecordParser has not been initialized.")
        return cls._global_instance

    @classmethod
    def set_global(cls) -> None:
        if cls._global_instance is None:
            cls._global_instance = LogRecordParser()
