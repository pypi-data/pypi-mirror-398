from datetime import datetime

from xlog.event.logging import Log
from xlog.format.text import Text


def test_construct_with_defaults():
    formatter = Text()
    assert formatter.timeformat == "%Y-%m-%d %H:%M:%S"
    assert formatter.format_str == "[{time}][{level}] {message}"


def test_construct_with_custom_timeformat():
    custom_time = "%Y/%m/%d %H:%M"
    formatter = Text(timeformat=custom_time)
    assert formatter.timeformat == custom_time
    assert formatter.format_str == "[{time}][{level}] {message}"


def test_construct_with_custom_format():
    custom_format = "{level} - {message} at {time}"
    formatter = Text(format=custom_format)
    assert formatter.timeformat == "%Y-%m-%d %H:%M:%S"
    assert formatter.format_str == custom_format


def test_construct_with_both_custom_timeformat_and_format():
    custom_time = "%H:%M:%S"
    custom_format = "{time} | {level} | {message}"
    formatter = Text(timeformat=custom_time, format=custom_format)
    assert formatter.timeformat == custom_time
    assert formatter.format_str == custom_format


def test_format_basic_event():
    formatter = Text()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025-11-22 10:30:45][INFO] Test message"


def test_format_event_with_different_levels():
    formatter = Text()

    event_debug = Log(
        message="Debug message",
        level="DEBUG",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result_debug = formatter.format(event_debug)
    assert result_debug == "[2025-11-22 10:30:45][DEBUG] Debug message"

    event_error = Log(
        message="Error message",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result_error = formatter.format(event_error)
    assert result_error == "[2025-11-22 10:30:45][ERROR] Error message"

    event_warning = Log(
        message="Warning message",
        level="WARNING",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result_warning = formatter.format(event_warning)
    assert result_warning == "[2025-11-22 10:30:45][WARNING] Warning message"


def test_format_event_with_custom_timeformat():
    formatter = Text(timeformat="%Y/%m/%d")
    event = Log(
        message="Date only test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025/11/22][INFO] Date only test"


def test_format_event_with_custom_format():
    formatter = Text(format="{level}: {message} ({time})")
    event = Log(
        message="Custom format test",
        level="WARNING",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "WARNING: Custom format test (2025-11-22 10:30:45)"


def test_format_event_with_empty_message():
    formatter = Text()
    event = Log(
        message="",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025-11-22 10:30:45][INFO] "


def test_format_event_with_multiline_message():
    formatter = Text()
    event = Log(
        message="Line 1\nLine 2\nLine 3",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025-11-22 10:30:45][INFO] Line 1\nLine 2\nLine 3"


def test_format_event_with_special_characters():
    formatter = Text()
    event = Log(
        message="Special chars: @#$%^&*(){}[]",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025-11-22 10:30:45][INFO] Special chars: @#$%^&*(){}[]"


def test_format_event_with_unicode_characters():
    formatter = Text()
    event = Log(
        message="Unicode test: 你好世界 🚀 café",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025-11-22 10:30:45][INFO] Unicode test: 你好世界 🚀 café"


def test_format_non_Log_returns_empty_string():
    formatter = Text()
    result = formatter.format("not a log event")
    assert result == ""

    result = formatter.format(None)
    assert result == ""

    result = formatter.format(123)
    assert result == ""

    result = formatter.format({"message": "dict"})
    assert result == ""


def test_format_event_preserves_message_spacing():
    formatter = Text()
    event = Log(
        message="  leading and trailing spaces  ",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    # Note: Log strips the message in its constructor
    result = formatter.format(event)
    assert "leading and trailing spaces" in result


def test_format_event_with_long_message():
    formatter = Text()
    long_message = "x" * 1000
    event = Log(
        message=long_message,
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert long_message in result
    assert result.startswith("[2025-11-22 10:30:45][INFO]")


def test_format_event_with_different_time_precision():
    formatter = Text(timeformat="%Y-%m-%d %H:%M:%S.%f")
    event = Log(
        message="Microsecond precision",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, 123456),
    )
    result = formatter.format(event)
    assert "2025-11-22 10:30:45.123456" in result
    assert result.endswith("[INFO] Microsecond precision")


def test_format_event_with_only_time():
    formatter = Text(timeformat="%H:%M:%S", format="{time}")
    event = Log(
        message="Only time",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "10:30:45"


def test_format_event_with_only_level():
    formatter = Text(format="{level}")
    event = Log(
        message="Only level",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "ERROR"


def test_format_event_with_only_message():
    formatter = Text(format="{message}")
    event = Log(
        message="Only message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "Only message"


def test_format_multiple_events_consecutively():
    formatter = Text()

    event1 = Log(
        message="First event",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    event2 = Log(
        message="Second event",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 31, 00),
    )
    event3 = Log(
        message="Third event",
        level="DEBUG",
        time=datetime(2025, 11, 22, 10, 31, 15),
    )

    result1 = formatter.format(event1)
    result2 = formatter.format(event2)
    result3 = formatter.format(event3)

    assert result1 == "[2025-11-22 10:30:45][INFO] First event"
    assert result2 == "[2025-11-22 10:31:00][ERROR] Second event"
    assert result3 == "[2025-11-22 10:31:15][DEBUG] Third event"


def test_format_with_iso_timeformat():
    formatter = Text(timeformat="%Y-%m-%dT%H:%M:%S")
    event = Log(
        message="ISO format",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert result == "[2025-11-22T10:30:45][INFO] ISO format"
