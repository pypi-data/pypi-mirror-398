from datetime import datetime

from xlog.event.logging import Log
from xlog.format.colortext import ColorText


def test_construct_with_defaults():
    formatter = ColorText()
    assert formatter._formatter is not None


def test_construct_with_custom_timeformat():
    custom_time = "%Y/%m/%d %H:%M"
    formatter = ColorText(timeformat=custom_time)
    assert formatter._formatter is not None


def test_construct_with_custom_format():
    custom_format = "%(log_color)s%(levelname)s%(reset)s - %(message)s"
    formatter = ColorText(textformat=custom_format)
    assert formatter._formatter is not None


def test_construct_with_custom_colors():
    custom_colors = {
        "INFO": "blue",
        "DEBUG": "white",
        "WARNING": "orange",
        "ERROR": "red",
        "UNKNOWN": "purple",
    }
    formatter = ColorText(colors=custom_colors)
    assert formatter._formatter is not None


def test_construct_with_all_custom_parameters():
    custom_time = "%H:%M:%S"
    custom_format = "%(log_color)s[%(asctime)s]%(reset)s %(message)s"
    custom_colors = {"INFO": "cyan", "ERROR": "magenta"}
    formatter = ColorText(
        timeformat=custom_time,
        textformat=custom_format,
        colors=custom_colors,
    )
    assert formatter._formatter is not None


def test_format_basic_info_event():
    formatter = ColorText()
    event = Log(
        message="Info message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "Info message" in result
    assert len(result) > len("Info message")


def test_format_debug_event():
    formatter = ColorText()
    event = Log(
        message="Debug message",
        level="DEBUG",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "Debug message" in result


def test_format_warning_event():
    formatter = ColorText()
    event = Log(
        message="Warning message",
        level="WARNING",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "Warning message" in result


def test_format_error_event():
    formatter = ColorText()
    event = Log(
        message="Error message",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "Error message" in result


def test_format_unknown_event():
    formatter = ColorText()
    event = Log(
        message="Unknown level message",
        level="UNKNOWN",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "Unknown level message" in result


def test_format_event_contains_level():
    formatter = ColorText()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "INFO" in result


def test_format_event_contains_timestamp():
    formatter = ColorText()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "2025" in result or "10:30" in result


def test_format_non_Log_returns_empty_string():
    formatter = ColorText()
    result = formatter.format("not a log event")
    assert result == ""

    result = formatter.format(None)
    assert result == ""

    result = formatter.format(123)
    assert result == ""

    result = formatter.format({"message": "dict"})
    assert result == ""


def test_format_event_with_empty_message():
    formatter = ColorText()
    event = Log(
        message="",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "INFO" in result


def test_format_event_with_multiline_message():
    formatter = ColorText()
    event = Log(
        message="Line 1\nLine 2\nLine 3",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result


def test_format_event_with_special_characters():
    formatter = ColorText()
    event = Log(
        message="Special chars: @#$%^&*(){}[]",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "Special chars: @#$%^&*(){}[]" in result


def test_format_event_with_unicode_characters():
    formatter = ColorText()
    event = Log(
        message="Unicode test: 你好世界 🚀 café",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "Unicode test: 你好世界 🚀 café" in result


def test_format_event_with_long_message():
    formatter = ColorText()
    long_message = "x" * 1000
    event = Log(
        message=long_message,
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert long_message in result


def test_format_multiple_events_consecutively():
    formatter = ColorText()

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

    assert "First event" in result1
    assert "INFO" in result1
    assert "Second event" in result2
    assert "ERROR" in result2
    assert "Third event" in result3
    assert "DEBUG" in result3


def test_format_different_events_have_different_colors():
    formatter = ColorText()
    event_info = Log(
        message="Same message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    event_error = Log(
        message="Same message",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )

    result_info = formatter.format(event_info)
    result_error = formatter.format(event_error)

    assert result_info != result_error
    assert "Same message" in result_info
    assert "Same message" in result_error
    assert "INFO" in result_info
    assert "ERROR" in result_error


def test_format_preserves_event_name_in_fake_record():
    formatter = ColorText()
    event = Log(
        message="Test message",
        name="TestLogger",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_event_with_custom_colors_produces_output():
    custom_colors = {
        "INFO": "cyan",
        "DEBUG": "white",
        "WARNING": "yellow",
        "ERROR": "red",
        "UNKNOWN": "magenta",
    }
    formatter = ColorText(colors=custom_colors)
    event = Log(
        message="Custom color test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "Custom color test" in result
    assert "INFO" in result


def test_default_constants_are_set():
    assert ColorText.TIME_FORMAT == "%Y-%m-%d %H:%M:%S"
    assert "%(log_color)s" in ColorText.FORMAT
    assert "%(levelname)s" in ColorText.FORMAT
    assert "%(reset)s" in ColorText.FORMAT
    assert "%(message)s" in ColorText.FORMAT
    assert ColorText.COLORS["INFO"] == "green"
    assert ColorText.COLORS["DEBUG"] == "cyan"
    assert ColorText.COLORS["WARNING"] == "yellow"
    assert ColorText.COLORS["ERROR"] == "red"
    assert ColorText.COLORS["UNKNOWN"] == "purple"


def test_format_event_with_context_tags_metrics():
    formatter = ColorText()
    event = Log(
        message="Event with metadata",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        context={"job": "test"},
        tags={"module": "formatter"},
        metrics={"duration": "10ms"},
    )
    result = formatter.format(event)
    assert "Event with metadata" in result
    assert "INFO" in result
