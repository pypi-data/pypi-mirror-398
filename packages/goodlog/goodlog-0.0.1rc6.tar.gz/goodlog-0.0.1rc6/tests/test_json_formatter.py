import json
import logging
from collections import OrderedDict
from unittest.mock import patch

from goodlog.formats import JSONFormatter, _standard_log_record_attributes


def test_standard_log_record_attributes_caching() -> None:
    """
    Test that standard_log_record_attributes uses LRU cache.
    """
    # First call should compute the result
    attrs1 = _standard_log_record_attributes()
    # Second call should return cached result
    attrs2 = _standard_log_record_attributes()

    # Should be the same object due to caching
    assert attrs1 is attrs2

    # Should contain standard LogRecord attributes
    expected_attrs = {
        "name",
        "msg",
        "args",
        "created",
        "msecs",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "processName",
        "process",
        "threadName",
        "thread",
        "relativeCreated",
        "getMessage",
        "taskName",
    }
    # Check that most expected attributes are present
    assert len(attrs1.intersection(expected_attrs)) > 15


def test_json_formatter_basic_fields() -> None:
    """
    Test that JSONFormatter includes basic required fields.
    """
    formatter = JSONFormatter()

    # Create a log record
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="/path/to/file.py",
        lineno=42,
        msg="Test message %s",
        args=("arg1",),
        exc_info=None,
    )

    # Format the record
    json_output = formatter.format(record)
    data = json.loads(json_output)

    # Check basic fields
    assert data["log_level"] == "INFO"
    assert data["message"] == "Test message arg1"
    assert data["logger_name"] == "test.logger"
    assert "timestamp" in data
    assert data["code_context"]["line_number"] == 42
    assert data["code_context"]["python_file_path"] == "/path/to/file.py"


def test_json_formatter_field_ordering() -> None:
    """
    Test that JSONFormatter maintains field order using OrderedDict.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test.logger",
        level=logging.WARNING,
        pathname="/test.py",
        lineno=10,
        msg="Test",
        args=(),
        exc_info=None,
    )

    json_output = formatter.format(record)

    # Parse JSON preserving order
    data = json.loads(json_output, object_pairs_hook=OrderedDict)

    # Check that primary fields come first in order
    keys = list(data.keys())
    assert keys[0] == "logger_name"
    assert keys[1] == "timestamp"
    assert keys[2] == "log_level"
    assert keys[3] == "message"


def test_json_formatter_funcname_handling() -> None:
    """
    Test function_name field handling - should omit when <module>.
    """
    formatter = JSONFormatter()

    # Test with funcName = "<module>" (should be omitted)
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Test",
        args=(),
        exc_info=None,
        func="<module>",  # This is the default
    )

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # function_name should not be included when it's "<module>"
    assert "function_name" not in data

    # Test with actual function name
    record.funcName = "my_function"
    json_output = formatter.format(record)
    data = json.loads(json_output)

    # funcName should be included ub function_name when it's not "<module>"
    assert data["code_context"].get("function_name") == "my_function"


def test_json_formatter_extra_info_field() -> None:
    """
    Test that extra_info field is included when present.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Test",
        args=(),
        exc_info=None,
    )

    # Add extra_info attribute
    record.extra_info = {"request_id": "123", "user": "testuser"}

    json_output = formatter.format(record)
    data = json.loads(json_output)

    assert "extra_info" in data
    assert data["extra_info"]["request_id"] == "123"
    assert data["extra_info"]["user"] == "testuser"


def test_json_formatter_exception_formatting() -> None:
    """
    Test exception formatting in JSON output.
    """
    formatter = JSONFormatter()

    # Create an exception
    try:
        raise ValueError("Test exception")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="/test.py",
        lineno=1,
        msg="Error occurred",
        args=(),
        exc_info=exc_info,
    )

    json_output = formatter.format(record)
    data = json.loads(json_output)

    assert "exception" in data
    assert "ValueError: Test exception" in data["exception"]
    assert "Traceback" in data["exception"]


def test_json_formatter_stack_info() -> None:
    """
    Test stack info field formatting.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="/test.py",
        lineno=1,
        msg="Warning",
        args=(),
        exc_info=None,
    )

    # Add stack info
    record.stack_info = (
        "Stack trace:\n  File test.py, line 10\n    some_function()"
    )

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # stack_info is now included directly
    assert "stack_info" in data
    assert "some_function()" in data["stack_info"]


def test_json_formatter_exc_text_field() -> None:
    """
    Test that exc_text field is included when present.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="/test.py",
        lineno=1,
        msg="Error",
        args=(),
        exc_info=None,
    )

    # Set exc_text (usually set by formatException)
    record.exc_text = "Formatted exception text"

    json_output = formatter.format(record)
    data = json.loads(json_output)

    assert "exc_text" in data
    assert data["exc_text"] == "Formatted exception text"


def test_json_formatter_extra_fields_from_logrecord() -> None:
    """
    Test that extra fields from LogRecord are included.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Test",
        args=(),
        exc_info=None,
    )

    # Add custom fields directly to the record (simulating extra={} parameter)
    record.custom_field1 = "value1"
    record.custom_field2 = 42
    record.custom_field3 = {"nested": "data"}
    record.custom_field4 = None  # Should be filtered out

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # Custom fields should be included
    assert data.get("custom_field1") == "value1"
    assert data.get("custom_field2") == 42
    assert data.get("custom_field3") == {"nested": "data"}

    # None values should be filtered out
    assert "custom_field4" not in data


def test_json_formatter_excludes_standard_attributes() -> None:
    """
    Test that standard LogRecord attributes are not duplicated in extra fields.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Test",
        args=(),
        exc_info=None,
    )

    # Add a custom field that shouldn't conflict
    record.my_custom_field = "custom_value"

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # Custom field should be present
    assert data.get("my_custom_field") == "custom_value"

    # Standard attributes shouldn't be duplicated
    # (they're either in specific fields or excluded)
    standard_attrs = _standard_log_record_attributes()
    for key in data.keys():
        if key in standard_attrs:
            # These are explicitly handled fields
            assert key in [
                "python_file_path",
                "lineno",
                "exc_text",
                "function_name",
            ]


def test_json_formatter_with_all_fields() -> None:
    """
    Test JSONFormatter with all possible fields populated.
    """
    formatter = JSONFormatter()

    # Create exception info
    try:
        raise RuntimeError("Test error")
    except RuntimeError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test.comprehensive",
        level=logging.ERROR,
        pathname="/path/to/comprehensive.py",
        lineno=999,
        msg="Comprehensive test with %s",
        args=("everything",),
        exc_info=exc_info,
        func="test_function",
    )

    # Add all optional fields
    record.extra_info = {"context": "test_context", "id": 12345}
    record.stack_info = "Stack trace information\n  at line 10"
    record.exc_text = "Pre-formatted exception text"
    record.custom_field = "custom_value"
    record.another_field = [1, 2, 3]

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # Verify all fields are present and correct
    assert data["log_level"] == "ERROR"
    assert data["message"] == "Comprehensive test with everything"
    assert data["logger_name"] == "test.comprehensive"
    assert (
        data["code_context"]["python_file_path"] == "/path/to/comprehensive.py"
    )
    assert data["code_context"]["line_number"] == 999
    assert data["code_context"]["function_name"] == "test_function"
    assert "timestamp" in data

    # Optional fields
    assert data["extra_info"]["context"] == "test_context"
    assert data["extra_info"]["id"] == 12345
    assert "exception" in data
    assert "RuntimeError: Test error" in data["exception"]
    assert data["stack_info"] == "Stack trace information\n  at line 10"
    assert data["exc_text"] == "Pre-formatted exception text"
    assert data["custom_field"] == "custom_value"
    assert data["another_field"] == [1, 2, 3]


def test_json_formatter_time_formatting() -> None:
    """
    Test that timestamp is properly formatted.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Test",
        args=(),
        exc_info=None,
    )

    # Mock formatTime to verify it's called
    with patch.object(
        formatter, "formatTime", return_value="2024-01-01 12:00:00"
    ) as mock_format_time:
        json_output = formatter.format(record)
        data = json.loads(json_output)

        # Verify formatTime was called with the record
        mock_format_time.assert_called_once_with(record)

        # Verify the timestamp in the output
        assert data["timestamp"] == "2024-01-01 12:00:00"


def test_json_formatter_none_values_filtered() -> None:
    """
    Test that None values are filtered out from output.
    """
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Test",
        args=(),
        exc_info=None,
    )

    # Add fields with None values
    record.none_field = None
    record.valid_field = "valid"
    record.zero_field = 0  # Should not be filtered
    record.empty_string = ""  # Should not be filtered
    record.false_field = False  # Should not be filtered

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # None should be filtered
    assert "none_field" not in data

    # Other falsy values should NOT be filtered
    assert data.get("valid_field") == "valid"
    assert data.get("zero_field") == 0
    assert data.get("empty_string") == ""
    assert data.get("false_field") is False


def test_json_formatter_message_formatting() -> None:
    """
    Test that getMessage() is used for message formatting.
    """
    formatter = JSONFormatter()

    # Test with args
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Hello %s, count: %d",
        args=("World", 42),
        exc_info=None,
    )

    json_output = formatter.format(record)
    data = json.loads(json_output)

    # Message should be formatted with args
    assert data["message"] == "Hello World, count: 42"

    # Test without args
    record2 = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/test.py",
        lineno=1,
        msg="Simple message",
        args=(),
        exc_info=None,
    )

    json_output2 = formatter.format(record2)
    data2 = json.loads(json_output2)

    assert data2["message"] == "Simple message"


def test_json_formatter_with_logger() -> None:
    """
    Test JSONFormatter integration with Python logger.
    """
    import io

    # Create a logger with JSONFormatter
    logger = logging.getLogger("test.json.formatter")
    logger.setLevel(logging.DEBUG)

    # Create a string stream handler
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    try:
        # Log various levels with extra fields
        logger.debug("Debug message", extra={"debug_field": "debug_value"})
        logger.info("Info message", extra={"info_field": 123})
        logger.warning("Warning message")
        logger.error("Error message", extra={"error_field": True})

        # Log with exception
        try:
            raise KeyError("Test key error")
        except KeyError:
            logger.exception("Exception occurred")

        # Get the output
        output = stream.getvalue()
        lines = output.strip().split("\n")

        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            assert "timestamp" in data
            assert "log_level" in data
            assert "message" in data
            assert "logger_name" in data

        # Verify specific messages
        messages = [json.loads(line) for line in lines]

        # Debug message
        debug_msg = messages[0]
        assert debug_msg["log_level"] == "DEBUG"
        assert debug_msg["message"] == "Debug message"
        assert debug_msg["debug_field"] == "debug_value"

        # Info message
        info_msg = messages[1]
        assert info_msg["log_level"] == "INFO"
        assert info_msg["info_field"] == 123

        # Warning message
        warning_msg = messages[2]
        assert warning_msg["log_level"] == "WARNING"

        # Error message
        error_msg = messages[3]
        assert error_msg["log_level"] == "ERROR"
        assert error_msg["error_field"] is True

        # Exception message
        exc_msg = messages[4]
        assert exc_msg["log_level"] == "ERROR"
        assert "exception" in exc_msg
        assert "KeyError" in exc_msg["exception"]

    finally:
        # Clean up
        logger.removeHandler(handler)
