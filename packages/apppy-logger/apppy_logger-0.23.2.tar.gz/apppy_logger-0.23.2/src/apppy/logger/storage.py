import contextvars
import logging
from typing import Any, Literal, Optional

LoggingStorageKey = Literal["request_id"]

# Define a context variable per key
_global_logging_vars: dict[str, contextvars.ContextVar[Any | None]] = {
    "request_id": contextvars.ContextVar("request_id", default=None),
}


class LoggingStorage(logging.Filter):
    _global_instance: Optional["LoggingStorage"] = None

    def add_request_id(self, request_id: str) -> str:
        _global_logging_vars["request_id"].set(request_id)
        return request_id

    def filter(self, record: logging.LogRecord) -> bool:
        stored_state = self.read_all()
        if hasattr(record, "state") and isinstance(record.state, dict):
            record.state.update(stored_state)  # type: ignore[invalid-assignment]
        else:
            record.state = stored_state

        return True

    def read(self, key: LoggingStorageKey) -> Any | None:
        return _global_logging_vars[key].get()

    def read_all(self) -> dict[str, Any]:
        return {
            key: value
            for key in _global_logging_vars
            if (value := _global_logging_vars[key].get()) is not None
        }

    def reset(self):
        # contextvars can't be "deleted", so just reset to None
        for key in _global_logging_vars:
            _global_logging_vars[key].set(None)

    @classmethod
    def get_global(cls) -> "LoggingStorage":
        if cls._global_instance is None:
            raise RuntimeError("LoggingStorage has not been initialized.")
        return cls._global_instance

    @classmethod
    def set_global(cls) -> None:
        if cls._global_instance is None:
            cls._global_instance = LoggingStorage()

    @staticmethod
    def apply(logger: logging.Logger):
        logger.addFilter(LoggingStorage.get_global())

    @staticmethod
    def apply_all():
        logger_dict = logging.Logger.manager.loggerDict
        for logger_name in logger_dict:
            logger = logger_dict.get(logger_name)
            if isinstance(logger, logging.Logger):
                LoggingStorage.apply(logger)
