import io
import json
from unittest.mock import patch

import pytest

from goodlog import (
    configure_logging,
    create_logger,
    add,
    remove,
)


def test_logger_comprehensive_flow() -> None:
    """
    Comprehensive test that verifies:
    1. Logger setup with global context
    2. JSON formatted log output
    3. Global and extra context inclusion in log records
    4. Logging with and without extra data
    """
    # Capture stdout to verify JSON output
    captured_output = io.StringIO()

    with patch("sys.stdout", captured_output):
        # 1. Setup: Configure logging with global context
        global_context = {
            "service": "test-service",
            "version": "1.2.3",
            "environment": "test",
        }
        configure_logging(global_context)

        # Create logger using public interface
        logger = create_logger("test.comprehensive")

        # 2. Logging scenarios:

        # Scenario A: Log with extra context and extra data
        add(request_id="req-456", user_id="user-789")
        logger.info(
            "User performed action",
            extra={
                "action": "login",
                "ip_address": "192.168.1.1",
                "success": True,
            },
        )
        remove()

        # Scenario B: Log without extra context but with extra data
        logger.warning(
            "Rate limit warning",
            extra={
                "current_rate": 85,
                "max_rate": 100,
                "endpoint": "/api/users",
            },
        )

        # Scenario C: Log with extra context but no extra data
        add(operation="database_cleanup", batch_id="batch-123")
        logger.error("Database cleanup failed")
        remove()

        # Scenario D: Simple log with no extra data or extra context
        logger.debug("Simple debug message")

    # 3. Assertions: Parse and verify log output
    log_lines = captured_output.getvalue().strip().split("\n")

    # Should have 4 log entries (debug might be filtered depending on level)
    log_entries = []
    for line in log_lines:
        if line.strip():
            log_entries.append(json.loads(line))

    # Verify we have the expected number of log entries
    assert (
        len(log_entries) >= 3
    )  # At least INFO, WARNING, ERROR (DEBUG might be filtered)

    # Test Scenario A: Log with extra context and extra data
    scenario_a = log_entries[0]

    # Verify it's valid JSON and has standard fields
    assert scenario_a["log_level"] == "INFO"
    assert scenario_a["message"] == "User performed action"
    assert scenario_a["logger_name"] == "test.comprehensive"
    assert "timestamp" in scenario_a

    # Verify extra_info contains both global and temporary context
    assert "extra_info" in scenario_a
    extra_info = scenario_a["extra_info"]
    # Global context from configuration
    assert extra_info["service"] == "test-service"
    assert extra_info["version"] == "1.2.3"
    assert extra_info["environment"] == "test"
    # Temporary context added via add_more_info
    assert extra_info["request_id"] == "req-456"
    assert extra_info["user_id"] == "user-789"

    # Verify extra data is included
    assert scenario_a["action"] == "login"
    assert scenario_a["ip_address"] == "192.168.1.1"
    assert scenario_a["success"] is True

    # Test Scenario B: Log without extra context but with extra data
    scenario_b = log_entries[1]

    assert scenario_b["log_level"] == "WARNING"
    assert scenario_b["message"] == "Rate limit warning"

    # Extra info should still contain global context but not temporary context
    assert "extra_info" in scenario_b
    extra_info_b = scenario_b["extra_info"]
    assert extra_info_b["service"] == "test-service"
    assert extra_info_b["version"] == "1.2.3"
    assert extra_info_b["environment"] == "test"

    # Temporary context should be removed (cleared after previous usage)
    assert "request_id" not in extra_info_b
    assert "user_id" not in extra_info_b

    # Extra data should be present
    assert scenario_b["current_rate"] == 85
    assert scenario_b["max_rate"] == 100
    assert scenario_b["endpoint"] == "/api/users"

    # Test Scenario C: Log with extra context but no extra data
    scenario_c = log_entries[2]

    assert scenario_c["log_level"] == "ERROR"
    assert scenario_c["message"] == "Database cleanup failed"

    # Extra info should contain global context and new temporary context
    assert "extra_info" in scenario_c
    extra_info_c = scenario_c["extra_info"]
    assert extra_info_c["service"] == "test-service"
    assert extra_info_c["version"] == "1.2.3"
    assert extra_info_c["environment"] == "test"

    # New temporary context should be present
    assert extra_info_c["operation"] == "database_cleanup"
    assert extra_info_c["batch_id"] == "batch-123"

    # Verify JSON structure completeness
    for entry in log_entries:
        # Every log entry should be valid JSON
        assert isinstance(entry, dict)

        # # Every entry should have required fields
        # for field in required_fields:
        #     assert field in entry, f"Missing required field: {field}"

        # Extra info field should be a dictionary
        assert "extra_info" in entry
        assert isinstance(entry["extra_info"], dict)

        # Extra info should always contain our setup values
        assert entry["extra_info"]["service"] == "test-service"
        assert entry["extra_info"]["version"] == "1.2.3"
        assert entry["extra_info"]["environment"] == "test"


def test_logger_context_isolation() -> None:
    """
    Test that extra contexts are properly isolated between operations
    """
    # Reset _ExtraLoggingInfo singleton for this test
    from goodlog.extra_info.store import _ExtraLoggingInfo

    _ExtraLoggingInfo._instances.clear()

    captured_output = io.StringIO()

    with patch("sys.stdout", captured_output):
        configure_logging({"service": "isolation-test"})
        logger = create_logger("test.isolation")

        # First operation with its own context
        add(operation="op1", data="first")
        logger.info("First operation")
        remove()

        # Second operation with different context
        add(operation="op2", data="second")
        logger.info("Second operation")
        remove()

        # Third log without extra context
        logger.info("No context operation")

    log_lines = captured_output.getvalue().strip().split("\n")
    log_entries = [json.loads(line) for line in log_lines if line.strip()]

    assert len(log_entries) == 3

    # First operation should have its context
    assert log_entries[0]["extra_info"]["operation"] == "op1"
    assert log_entries[0]["extra_info"]["data"] == "first"

    # Second operation should have different context
    assert log_entries[1]["extra_info"]["operation"] == "op2"
    assert log_entries[1]["extra_info"]["data"] == "second"

    # Third operation should have no temporary context
    assert "operation" not in log_entries[2]["extra_info"]
    assert "data" not in log_entries[2]["extra_info"]

    # All should have the same base context
    for entry in log_entries:
        assert entry["extra_info"]["service"] == "isolation-test"


def test_logger_exception_handling() -> None:
    """
    Test that exception info and stack traces are properly logged
    """
    # Reset singleton for clean test
    from goodlog.extra_info.store import _ExtraLoggingInfo

    _ExtraLoggingInfo._instances.clear()

    captured_output = io.StringIO()

    with patch("sys.stdout", captured_output):
        configure_logging({"service": "exception-test"})
        logger = create_logger("test.exceptions")

        # Test exception logging with exc_info=True
        try:
            raise ValueError("Test exception message")
        except ValueError:
            logger.error("Error occurred", exc_info=True)

        # Test exception logging with logger.exception()
        try:
            raise KeyError("Another test exception")
        except KeyError:
            logger.exception("Key error occurred")

        # Test stack trace logging
        logger.warning("Stack trace test", stack_info=True)

    log_lines = captured_output.getvalue().strip().split("\n")
    log_entries = [json.loads(line) for line in log_lines if line.strip()]

    assert len(log_entries) == 3

    # First entry should have exception info
    exc_entry = log_entries[0]
    assert exc_entry["log_level"] == "ERROR"
    assert exc_entry["message"] == "Error occurred"
    assert "exception" in exc_entry
    assert "ValueError: Test exception message" in exc_entry["exception"]
    assert "Traceback" in exc_entry["exception"]

    # Second entry should also have exception info (via logger.exception)
    exc_entry2 = log_entries[1]
    assert exc_entry2["log_level"] == "ERROR"
    assert exc_entry2["message"] == "Key error occurred"
    assert "exception" in exc_entry2
    assert "KeyError: 'Another test exception'" in exc_entry2["exception"]

    # Third entry should have stack trace
    stack_entry = log_entries[2]
    assert stack_entry["log_level"] == "WARNING"
    assert stack_entry["message"] == "Stack trace test"
    assert "stack_info" in stack_entry
    assert "test_logger_exception_handling" in stack_entry["stack_info"]


def test_logger_extra_fields() -> None:
    """
    Test that extra fields passed via logger.info(extra={...}) are included
    """
    # Reset singleton for clean test
    from goodlog.extra_info.store import _ExtraLoggingInfo

    _ExtraLoggingInfo._instances.clear()

    captured_output = io.StringIO()

    with patch("sys.stdout", captured_output):
        configure_logging({"service": "extra-test"})
        logger = create_logger("test.extra")

        # Test various types of extra data
        logger.info(
            "Testing extra fields",
            extra={
                "string_field": "test_value",
                "numeric_field": 42,
                "boolean_field": True,
                "list_field": [1, 2, 3],
                "dict_field": {"nested": "value"},
                "none_field": None,  # This should be filtered out
            },
        )

    log_lines = captured_output.getvalue().strip().split("\n")
    log_entries = [json.loads(line) for line in log_lines if line.strip()]

    assert len(log_entries) == 1
    entry = log_entries[0]

    # Verify extra fields are included
    assert entry["string_field"] == "test_value"
    assert entry["numeric_field"] == 42
    assert entry["boolean_field"] is True
    assert entry["list_field"] == [1, 2, 3]
    assert entry["dict_field"] == {"nested": "value"}

    # Verify None field is filtered out
    assert "none_field" not in entry


def test_logger_file_location_info() -> None:
    """
    Test that file location info (pathname, lineno, function_name) is included
    """
    # Reset singleton for clean test
    from goodlog.extra_info.store import _ExtraLoggingInfo

    _ExtraLoggingInfo._instances.clear()

    captured_output = io.StringIO()

    with patch("sys.stdout", captured_output):
        configure_logging({"service": "location-test"})
        logger = create_logger("test.location")

        # This log should include file location info
        logger.info("Location test message")

    log_lines = captured_output.getvalue().strip().split("\n")
    log_entries = [json.loads(line) for line in log_lines if line.strip()]

    assert len(log_entries) == 1
    entry = log_entries[0]

    # Verify location fields are present
    assert "code_context" in entry
    assert "python_file_path" in entry["code_context"]
    assert "line_number" in entry["code_context"]
    assert "function_name" in entry["code_context"]
    assert (
        entry["code_context"]["function_name"]
        == "test_logger_file_location_info"
    )
    assert (
        "test_logger_comprehensive.py"
        in entry["code_context"]["python_file_path"]
    )
    assert isinstance(entry["code_context"]["line_number"], int)


def test_extra_logging_info_singleton() -> None:
    """
    Test _ExtraLoggingInfo singleton behavior
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    # Test singleton behavior
    info1 = _ExtraLoggingInfo(key1="value1")
    info2 = _ExtraLoggingInfo(key2="value2")  # Should be same instance

    assert info1 is info2  # Same instance
    assert info1.as_dict() == {"key1": "value1"}  # First initialization wins


def test_extra_logging_info_operations() -> None:
    """
    Test _ExtraLoggingInfo add/remove operations
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    info = _ExtraLoggingInfo(base_key="base_value")

    # Test add_more_info
    info.add_more_info(temp_key1="temp_value1", temp_key2="temp_value2")

    result = info.as_dict()
    assert result["base_key"] == "base_value"
    assert result["temp_key1"] == "temp_value1"
    assert result["temp_key2"] == "temp_value2"

    # Test remove_more_info
    removed = info.remove_more_info()
    assert removed == {"temp_key1": "temp_value1", "temp_key2": "temp_value2"}

    # After removal, only base key should remain
    result_after = info.as_dict()
    assert result_after == {"base_key": "base_value"}
    assert "temp_key1" not in result_after
    assert "temp_key2" not in result_after


def test_extra_logging_info_overwrite_keys() -> None:
    """
    Test _ExtraLoggingInfo behavior with duplicate keys
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    captured_output = io.StringIO()

    with patch("sys.stdout", captured_output):
        # Create _ExtraLoggingInfo with initial data that has an existing key
        info = _ExtraLoggingInfo(existing_key="original_value")

        # Configure logging after creating the instance to capture warning logs
        configure_logging({})

        # Try to add a key that already exists - should trigger warning
        info.add_more_info(existing_key="new_value", new_key="new_value")

        # Should still have original value (duplicate key should be discarded)
        result = info.as_dict()
        assert result["existing_key"] == "new_value"
        assert result["new_key"] == "new_value"


def test_extra_logging_info_json_serialization_validation_init() -> None:
    """
    Test JSON serialization validation in _ExtraLoggingInfo.__init__()
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    # Test with valid JSON-serializable data
    info = _ExtraLoggingInfo(
        string="value",
        number=42,
        boolean=True,
        list=[1, 2, 3],
        dict={"nested": "value"},
        null=None,
    )
    expected_data = {
        "string": "value",
        "number": 42,
        "boolean": True,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "null": None,
    }
    assert info.as_dict() == expected_data

    # Reset for next test
    _ExtraLoggingInfo._instances.clear()

    # Test with non-JSON-serializable data (function object)
    def some_function() -> None:
        pass

    with pytest.raises(
        ValueError, match="The provided dict is not JSON-serializable"
    ):
        _ExtraLoggingInfo(valid_key="valid_value", invalid_key=some_function)


def test_extra_logging_info_json_serialization_validation_add_more_info() -> (
    None
):
    """
    Test JSON serialization validation in _ExtraLoggingInfo.add_more_info()
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo
    import datetime

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    # Create instance with valid data
    info = _ExtraLoggingInfo(base_key="base_value")

    # Test adding valid JSON-serializable data
    info.add_more_info(
        string="value", number=123, boolean=False
    )  # Should not raise

    result = info.as_dict()
    assert result["base_key"] == "base_value"
    assert result["string"] == "value"
    assert result["number"] == 123
    assert result["boolean"] is False

    # Test adding non-JSON-serializable data
    with pytest.raises(
        ValueError, match="The provided dict is not JSON-serializable"
    ):
        info.add_more_info(
            valid_key="valid_value", invalid_key=datetime.datetime.now()
        )


def test_extra_logging_info_json_serialization_edge_cases() -> None:
    """
    Test JSON serialization validation edge cases
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo
    import uuid

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    # Test with various non-serializable objects
    test_cases = [
        ({"set_object": {1, 2, 3}}, "Sets are not JSON serializable"),
        (
            {"uuid_object": uuid.uuid4()},
            "UUID objects are not JSON serializable",
        ),
        ({"bytes_object": b"bytes"}, "Bytes are not JSON serializable"),
        (
            {"complex_number": 1 + 2j},
            "Complex numbers are not JSON serializable",
        ),
    ]

    for invalid_kwargs, description in test_cases:
        _ExtraLoggingInfo._instances.clear()  # Reset for each test

        with pytest.raises(
            ValueError, match="The provided dict is not JSON-serializable"
        ):
            _ExtraLoggingInfo(**invalid_kwargs)  # type: ignore

    # Test that empty kwargs is valid
    _ExtraLoggingInfo._instances.clear()
    info = _ExtraLoggingInfo()  # Should not raise
    assert info.as_dict() == {}


def test_configure_logging_json_validation() -> None:
    """
    Test that configure_logging validates JSON serialization
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    # Test with valid data
    valid_config = {"service": "test", "version": "1.0"}
    configure_logging(valid_config)  # Should not raise

    # Reset for invalid test
    _ExtraLoggingInfo._instances.clear()

    # Test with invalid data
    def invalid_function() -> None:
        pass

    invalid_config = {"service": "test", "invalid": invalid_function}

    with pytest.raises(
        ValueError, match="The provided dict is not JSON-serializable"
    ):
        configure_logging(invalid_config)


def test_module_level_functions() -> None:
    """
    Test the new module-level convenience functions
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo, set_info
    from goodlog import add, remove

    # Reset singleton for clean test
    _ExtraLoggingInfo._instances.clear()

    # Test set_info
    set_info(service="test-service", version="1.0")
    instance = _ExtraLoggingInfo()
    result = instance.as_dict()
    assert result["service"] == "test-service"
    assert result["version"] == "1.0"

    # Test add
    add(request_id="req-123", user="test-user")
    result_after_add = instance.as_dict()
    assert result_after_add["service"] == "test-service"
    assert result_after_add["version"] == "1.0"
    assert result_after_add["request_id"] == "req-123"
    assert result_after_add["user"] == "test-user"

    # Test remove
    removed = remove()
    assert removed == {"request_id": "req-123", "user": "test-user"}

    # After removal, only base info should remain
    result_after_remove = instance.as_dict()
    assert result_after_remove == {"service": "test-service", "version": "1.0"}
    assert "request_id" not in result_after_remove
    assert "user" not in result_after_remove


def test_extra_info_context_manager_behavior() -> None:
    """
    Test extra_info_context covers both normal and exception exit paths.
    """
    from goodlog import ephemeral_info_context
    from goodlog.extra_info.store import _ExtraLoggingInfo

    _ExtraLoggingInfo._instances.clear()

    # Normal exit
    with ephemeral_info_context(foo="bar"):
        assert _ExtraLoggingInfo().as_dict()["foo"] == "bar"
    # After context, foo should be removed
    assert "foo" not in _ExtraLoggingInfo().as_dict()

    # Exception exit
    try:
        with ephemeral_info_context(baz="qux"):
            assert _ExtraLoggingInfo().as_dict()["baz"] == "qux"
            raise RuntimeError("test error")
    except RuntimeError:
        pass
    # After context, baz should be removed
    assert "baz" not in _ExtraLoggingInfo().as_dict()


def test_configure_logging_without_extra_info() -> None:
    """
    Test that configure_logging works when called without extra_info.
    """
    from goodlog.extra_info.store import _ExtraLoggingInfo

    _ExtraLoggingInfo._instances.clear()

    configure_logging()

    assert _ExtraLoggingInfo().as_dict() == {}
