import logging
import re
import sys

from zoho_projects_sdk.utils.logger import get_logger


def test_get_logger_returns_logger_instance() -> None:
    """
    Test that get_logger returns a logging.Logger instance.
    """
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)


def test_get_logger_sets_correct_level() -> None:
    """
    Test that get_logger sets the logger level to INFO.
    """
    logger = get_logger("test_logger_level")
    assert logger.level == logging.INFO


def test_get_logger_adds_stream_handler() -> None:
    """
    Test that get_logger adds a StreamHandler to the logger.
    """
    logger = get_logger("test_logger_handler")
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_get_logger_configures_formatter() -> None:
    """
    Test that get_logger configures the handler with the correct formatter.
    """
    logger = get_logger("test_logger_formatter")
    handler = logger.handlers[0]
    formatter = handler.formatter
    assert isinstance(formatter, logging.Formatter)

    # Create a log record to test the formatter
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)

    # Verify the formatted output contains expected components
    assert "test_logger" in formatted
    assert "INFO" in formatted
    assert "Test message" in formatted
    # Verify timestamp format (YYYY-MM-DD)
    assert re.search(r"\d{4}-\d{2}-\d{2}", formatted) is not None


def test_get_logger_uses_stdout() -> None:
    """
    Test that get_logger uses stdout for the StreamHandler.
    """
    logger = get_logger("test_logger_stdout")
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream is sys.stdout


def test_get_logger_reuses_existing_logger() -> None:
    """
    Test that get_logger returns the same logger instance for the same name.
    """
    logger1 = get_logger("test_logger_reuse")
    logger2 = get_logger("test_logger_reuse")
    assert logger1 is logger2


def test_get_logger_does_not_add_duplicate_handlers() -> None:
    """
    Test that get_logger doesn't add duplicate handlers to the same logger.
    """
    logger = get_logger("test_logger_duplicate")
    initial_handler_count = len(logger.handlers)

    # Call get_logger again for the same logger name
    get_logger("test_logger_duplicate")

    # Handler count should remain the same
    assert len(logger.handlers) == initial_handler_count


def test_get_logger_different_names_create_different_loggers() -> None:
    """
    Test that get_logger creates different logger instances for different names.
    """
    logger1 = get_logger("test_logger_1")
    logger2 = get_logger("test_logger_2")
    assert logger1 is not logger2
    assert logger1.name != logger2.name


def test_logger_functionality() -> None:
    """
    Test that the logger actually works for logging messages.
    """
    logger = get_logger("test_logger_functionality")

    # Test that we can log a message without errors
    # This should not raise an exception
    try:
        logger.info("Test message")
    except (RuntimeError, OSError, ValueError) as e:
        assert False, f"Logger should not raise exception: {e}"
