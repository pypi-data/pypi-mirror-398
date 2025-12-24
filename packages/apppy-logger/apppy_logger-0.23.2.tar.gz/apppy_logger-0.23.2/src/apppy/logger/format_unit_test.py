import logging
from logging import LogRecord

from apppy.logger.format import ExtraLoggingFormatter, datefmt_default, fmt_default
from apppy.logger.parser import LogRecordParser
from apppy.logger.storage import LoggingStorage

LogRecordParser.set_global()
LoggingStorage.set_global()


def test_format_no_extra():
    formatter: ExtraLoggingFormatter = ExtraLoggingFormatter(
        fmt=fmt_default, datefmt=datefmt_default
    )

    logger = logging.Logger("test_format_no_extra")
    record: LogRecord = logger.makeRecord(
        name="test_format_no_extra",
        level=logging.INFO,
        fn="test_format_no_extra",
        lno=19,
        msg="test_format_no_extra message",
        args=None,
        exc_info=None,
    )
    msg = formatter.format(record)
    assert msg.endswith(
        "| INFO | test_format_no_extra | test_format_no_extra message"
    ), f"Unexpected formatted msg: {msg}"


def test_format_with_extra():
    formatter: ExtraLoggingFormatter = ExtraLoggingFormatter(
        fmt=fmt_default, datefmt=datefmt_default
    )

    logger = logging.Logger("test_format_with_extra")
    record: LogRecord = logger.makeRecord(
        name="test_format_with_extra",
        level=logging.INFO,
        fn="test_format_with_extra",
        lno=19,
        msg="test_format_with_extra message",
        args=None,
        exc_info=None,
        extra={"extra": "value"},
    )
    msg = formatter.format(record)
    assert msg.endswith(
        "| INFO | test_format_with_extra | test_format_with_extra message | extra=value"
    ), f"Unexpected formatted msg: {msg}"


def test_format_with_extra_multiple():
    formatter: ExtraLoggingFormatter = ExtraLoggingFormatter(
        fmt=fmt_default, datefmt=datefmt_default
    )

    logger = logging.Logger("test_format_with_extra_multiple")
    record: LogRecord = logger.makeRecord(
        name="test_format_with_extra_multiple",
        level=logging.INFO,
        fn="test_format_with_extra_multiple",
        lno=19,
        msg="test_format_with_extra_multiple message",
        args=None,
        exc_info=None,
        extra={"extra1": "value1", "extra2": "value2"},
    )
    msg = formatter.format(record)
    assert msg.endswith(
        "| INFO | test_format_with_extra_multiple | test_format_with_extra_multiple message | extra1=value1 | extra2=value2"  # noqa: E501
    ), f"Unexpected formatted msg: {msg}"


def test_format_with_storage_state():
    formatter: ExtraLoggingFormatter = ExtraLoggingFormatter(
        fmt=fmt_default, datefmt=datefmt_default
    )

    logger = logging.Logger("test_format_with_storage_state")
    record: LogRecord = logger.makeRecord(
        name="test_format_with_storage_state",
        level=logging.INFO,
        fn="test_format_with_storage_state",
        lno=19,
        msg="test_format_with_storage_state message",
        args=None,
        exc_info=None,
    )

    LoggingStorage.get_global().add_request_id("test_format_with_storage_state_request")
    LoggingStorage.get_global().filter(record)
    msg = formatter.format(record)
    LoggingStorage.get_global().reset()

    assert msg.endswith(
        "| INFO | test_format_with_storage_state | test_format_with_storage_state message | request_id=test_format_with_storage_state_request"  # noqa: E501
    ), f"Unexpected formatted msg: {msg}"


def test_format_with_storage_state_and_extra():
    formatter: ExtraLoggingFormatter = ExtraLoggingFormatter(
        fmt=fmt_default, datefmt=datefmt_default
    )

    logger = logging.Logger("test_format_with_storage_state_and_extra")
    record: LogRecord = logger.makeRecord(
        name="test_format_with_storage_state_and_extra",
        level=logging.INFO,
        fn="test_format_with_storage_state_and_extra",
        lno=19,
        msg="test_format_with_storage_state_and_extra message",
        args=None,
        exc_info=None,
        extra={"extra": "value"},
    )

    LoggingStorage.get_global().add_request_id("test_format_with_storage_state_and_extra_request")
    LoggingStorage.get_global().filter(record)
    msg = formatter.format(record)
    LoggingStorage.get_global().reset()

    assert msg.endswith(
        "| INFO | test_format_with_storage_state_and_extra | test_format_with_storage_state_and_extra message | request_id=test_format_with_storage_state_and_extra_request | extra=value"  # noqa: E501
    ), f"Unexpected formatted msg: {msg}"
