import logging
import sys
from pathlib import Path
import pytest
from gdutils.utils.logger import (
    SimpleFormatter,
    HtmlFormatter,
    CSVFormatter,
    get_logger,
    get_csv_logger,
    stream_csv_handler,
)

class TestSimpleFormatter:
    def test_init_sets_format(self):
        formatter = SimpleFormatter(origin=True)
        # Check if style is set to '{' which is done in super().__init__
        # We can check the format string itself roughly
        assert "{color}" in formatter._fmt
        assert "{message}" in formatter._fmt
        assert "{name}" in formatter._fmt

        formatter_no_origin = SimpleFormatter(origin=False)
        assert "{name}" not in formatter_no_origin._fmt

    def test_format_debug_message(self):
        formatter = SimpleFormatter(origin=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.DEBUG,
            pathname=__file__,
            lineno=10,
            msg="debug message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        # Check for color codes and message
        assert "\x1b[;1m" in output  # DEBUG color
        assert "debug message" in output
        assert "DEBUG" in output

    def test_format_with_origin(self):
        formatter = SimpleFormatter(origin=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="info message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        output = formatter.format(record)
        assert "test_logger" in output
        assert "test_func" in output
        assert "info message" in output

    def test_format_module_func_name(self):
        formatter = SimpleFormatter(origin=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="message",
            args=(),
            exc_info=None,
            func="<module>",
        )
        output = formatter.format(record)
        assert "test_logger" in output
        assert "<module>" not in output

    def test_format_no_side_effects(self):
        formatter = SimpleFormatter(origin=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        # Create a copy of dict to compare later
        original_dict = record.__dict__.copy()
        
        formatter.format(record)
        
        # Verify the record was not modified
        assert record.funcName == "test_func"
        assert record.levelname == "INFO"
        assert record.__dict__ == original_dict

class TestHtmlFormatter:
    def test_format_html(self):
        formatter = HtmlFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=10,
            msg="error message\nline 2",
            args=(),
            exc_info=None,
            func="test_func",
        )
        output = formatter.format(record)
        assert '<font color="Red">' in output
        assert "error message" in output
        assert "<br>" in output # Newline replacement
        assert "line 2" in output
        assert "test_logger (test_func)" in output

class TestCSVFormatter:
    def test_format_csv(self):
        formatter = CSVFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="csv message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        output = formatter.format(record)
        # Default formats: asctime, levelname, funcName, message
        # We can't easily check asctime without mocking time, but we can check others
        assert "INFO" in output
        assert "test_func" in output
        assert "csv message" in output
        assert ", " in output # Default separator

    def test_custom_formats_and_sep(self):
        formatter = CSVFormatter(formats=["levelname", "message"], sep="|")
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname=__file__,
            lineno=10,
            msg="warning",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert output == "WARNING|warning"

@pytest.fixture(autouse=True)
def cleanup_logger():
    # Save original handlers
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)
    yield
    # Restore handlers
    logger.handlers = original_handlers

def test_get_logger_defaults(capsys):
    logger = get_logger(remove_handlers=True, default=True)
    logger.setLevel(logging.INFO) # Ensure INFO messages are processed
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, SimpleFormatter)
    
    logger.info("test output")
    captured = capsys.readouterr()
    assert "test output" in captured.out

def test_get_logger_logfile(tmp_path):
    log_file = tmp_path / "test.log"
    logger = get_logger(remove_handlers=True, default=False, logfile=str(log_file))
    
    assert len(logger.handlers) == 1
    # RotatingFileHandler inherits from BaseRotatingHandler -> FileHandler -> StreamHandler
    # But usually checks against specific class
    from logging.handlers import RotatingFileHandler
    assert isinstance(logger.handlers[0], RotatingFileHandler)
    assert isinstance(logger.handlers[0].formatter, CSVFormatter)
    
    logger.error("file error")
    
    # Force flush/close to ensure write
    for h in logger.handlers:
        h.close()
        
    content = log_file.read_text()
    assert "ERROR" in content
    assert "file error" in content

def test_get_logger_logfile_py_extension(tmp_path):
    # If .py is passed, it should switch to .log
    script_file = tmp_path / "script.py"
    expected_log = tmp_path / "script.log"
    
    logger = get_logger(remove_handlers=True, default=False, logfile=str(script_file))
    
    # We need to find the handler that writes to file
    file_handler = None
    from logging.handlers import RotatingFileHandler
    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler):
            file_handler = h
            break
            
    assert file_handler is not None
    # Check filename matches expected_log
    # Note: h.baseFilename is absolute
    assert Path(file_handler.baseFilename).resolve() == expected_log.resolve()
    
    file_handler.close()

def test_get_csv_logger(capsys):
    logger = get_csv_logger(formats=["message"], sep=";")
    logger.warning("csv log")
    
    captured = capsys.readouterr()
    assert "csv log" in captured.out
    # Since we only asked for message, it should just be the message (plus newline from handler)
    assert captured.out.strip() == "csv log"

def test_stream_csv_handler():
    handler = stream_csv_handler(formats=["levelname", "message"], sep=":")
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, CSVFormatter)
    
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg="msg", args=(), exc_info=None
    )
    output = handler.format(record)
    assert output == "INFO:msg"

