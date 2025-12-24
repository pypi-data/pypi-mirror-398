import logging


class SuppressApiLoggingFilter(logging.Filter):
    """
    Suppress HTTP logs to an API endpoint via its path.
    """

    def __init__(self, path: str):
        super().__init__(f"SuppressApiLoggingFilter_{path}")
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1

    @classmethod
    def apply(cls, logger: logging.Logger, path: str):
        filter = cls(path)
        logger.addFilter(filter)
