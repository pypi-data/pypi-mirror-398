import logging
import sys

from apppy.logger.filter import SuppressApiLoggingFilter
from apppy.logger.format import ExtraLoggingFormatter, NewLineTerminator
from apppy.logger.parser import LogRecordParser
from apppy.logger.storage import LoggingStorage


def bootstrap_global_logging(level, stdout=False):
    """
    Utility to apply custom logging configuration
    to application loggers. It should be called very
    early in the application boot process.
    """
    if isinstance(level, str):
        level = logging._nameToLevel[level.upper()]

    logging.root.setLevel(level)

    if stdout:
        # Configure the logging system to use stdout.
        # This should be used for frameworks with minimal logging configuration (e.g. AWS Lambda)
        # For mature application frameworks (e.g. uvicorn), do not use the stdout flag.
        logging.basicConfig(level=level, handlers=[logging.StreamHandler(sys.stdout)], force=True)

    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("httpcore.connection").setLevel(logging.INFO)
    logging.getLogger("httpcore.http11").setLevel(logging.INFO)

    # Setup global singletons
    LogRecordParser.set_global()
    LoggingStorage.set_global()
    # Apply formatters to all loggers so that their
    # output is uniform
    ExtraLoggingFormatter.apply(logging.root)
    ExtraLoggingFormatter.apply_all()
    # Setup the filter to add Logging Storage state
    # to each log record
    LoggingStorage.apply_all()

    if stdout:
        # If we configured stdout (see comment above) then
        # ensure logs go on separate lines
        NewLineTerminator.apply_all()

    # A /health endpoint is typically called a lot in deployed environments
    # as part of load balancer checks. This bloats the application logs
    # so this filter allows health checks to be skipped in logs.
    SuppressApiLoggingFilter.apply(logging.getLogger("uvicorn.access"), "/health")


class WithLogger:
    """
    Class decorator that injects a _logger object using a very standard
    naming convention. The convention is based on the class name so that
    log lines can be easily associated with a given class. For example:

    class MyService(WithLogger):
        ...
        def do_something(self):
            # This logger will be named with the module and class names
            # e.g. 'module.path.to.MyService'
            self._logger.info("I am doing something")
        ...
    """

    _logger: logging.Logger

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._logger = logging.getLogger(f"{cls.__module__}.{cls.__qualname__}")
