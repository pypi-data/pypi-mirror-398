import logging

from apppy.logger.parser import LogRecordParser

fmt_default = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
datefmt_default = "%Y-%m-%dT%H:%M:%SZ%z"


class ExtraLoggingFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        message = super().format(record)

        state_info = LogRecordParser.get_global().parse_state_info(record)
        if state_info:
            state_str = " | ".join(f"{key}={value}" for key, value in state_info.items())
            message = f"{message} | {state_str}"

        extra_info = LogRecordParser.get_global().parse_extra_info(record)
        if extra_info:
            extra_str = " | ".join(f"{key}={value}" for key, value in extra_info.items())
            message = f"{message} | {extra_str}"

        return message

    @classmethod
    def apply(cls, logger: logging.Logger, fmt: str = fmt_default, datefmt: str = datefmt_default):
        # Check if the logger has any handlers and add a default if none exist
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            logger.addHandler(handler)

        # Apply formatter to all handlers
        formatter = cls(fmt=fmt, datefmt=datefmt)
        for h in logger.handlers:
            h.setFormatter(formatter)

    @classmethod
    def apply_all(cls, fmt: str = fmt_default, datefmt: str = datefmt_default):
        logger_dict = logging.Logger.manager.loggerDict
        for logger_name in logger_dict:
            logger = logger_dict.get(logger_name)
            if isinstance(logger, logging.Logger):
                ExtraLoggingFormatter.apply(logger, fmt=fmt, datefmt=datefmt)


class NewLineTerminator:
    @classmethod
    def apply(cls, logger: logging.Logger):
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.terminator = "\n"

    @classmethod
    def apply_all(cls):
        logger_dict = logging.Logger.manager.loggerDict
        for logger_name in logger_dict:
            logger = logger_dict.get(logger_name)
            if isinstance(logger, logging.Logger):
                NewLineTerminator.apply(logger)
