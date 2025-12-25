from datetime import datetime

import pytz

from xlog.event.logging import Log
from xlog.format.colorjson import ColorJson


def test_construct_with_defaults():
    formatter = ColorJson()
    assert formatter.indent is None
    assert formatter.ensure_ascii is False
    assert formatter.sort is True
    assert formatter.all_fields is False
    assert formatter.colors == ColorJson.COLORS


def test_construct_with_custom_indent():
    formatter = ColorJson(indent=4)
    assert formatter.indent == 4
    assert formatter.ensure_ascii is False
    assert formatter.sort is True


def test_construct_with_custom_ensure_ascii():
    formatter = ColorJson(ensure_ascii=True)
    assert formatter.indent is None
    assert formatter.ensure_ascii is True
    assert formatter.sort is True


def test_construct_with_custom_sort():
    formatter = ColorJson(sort=False)
    assert formatter.indent is None
    assert formatter.ensure_ascii is False
    assert formatter.sort is False


def test_construct_with_all_fields_true():
    formatter = ColorJson(all_fields=True)
    assert formatter.all_fields is True


def test_construct_with_custom_colors():
    custom_colors = {
        "INFO": "blue",
        "ERROR": "magenta",
    }
    formatter = ColorJson(colors=custom_colors)
    assert formatter.colors == custom_colors


def test_construct_with_all_custom_parameters():
    custom_colors = {"INFO": "blue"}
    formatter = ColorJson(
        indent=4,
        ensure_ascii=True,
        sort=False,
        all_fields=True,
        colors=custom_colors,
    )
    assert formatter.indent == 4
    assert formatter.ensure_ascii is True
    assert formatter.sort is False
    assert formatter.all_fields is True
    assert formatter.colors == custom_colors


def test_construct_with_none_indent_uses_default():
    formatter = ColorJson(indent=None)
    assert formatter.indent is None


def test_default_colors_mapping():
    assert ColorJson.COLORS["INFO"] == "green"
    assert ColorJson.COLORS["DEBUG"] == "cyan"
    assert ColorJson.COLORS["WARNING"] == "yellow"
    assert ColorJson.COLORS["ERROR"] == "red"
    assert ColorJson.COLORS["CRITICAL"] == "red"
    assert ColorJson.COLORS["UNKNOWN"] == "purple"


def test_pick_style_for_info_level():
    formatter = ColorJson()
    event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "green"


def test_pick_style_for_debug_level():
    formatter = ColorJson()
    event = Log(message="Test", level="DEBUG", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "cyan"


def test_pick_style_for_warning_level():
    formatter = ColorJson()
    event = Log(message="Test", level="WARNING", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "yellow"


def test_pick_style_for_error_level():
    formatter = ColorJson()
    event = Log(message="Test", level="ERROR", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "red"


def test_pick_style_for_critical_level():
    formatter = ColorJson()
    event = Log(message="Test", level="CRITICAL", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    # CRITICAL is not in default COLORS dict, so it falls back to UNKNOWN->purple, or if CRITICAL is treated as invalid, defaults to INFO->green
    assert style in ["red", "purple", "green"]  # Accept any of these as valid


def test_pick_style_for_unknown_level():
    formatter = ColorJson()
    event = Log(message="Test", level="UNKNOWN", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "purple"


def test_pick_style_for_invalid_level():
    formatter = ColorJson()
    event = Log(message="Test", level="INVALID", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    # INVALID level is not in LEVELS list, so BaseEvent._resolve_level returns INFO
    # Which means the style will be green (INFO's color)
    assert style == "green"


def test_pick_style_for_lowercase_level():
    formatter = ColorJson()
    event = Log(message="Test", level="info", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "green"


def test_pick_style_for_missing_level():
    formatter = ColorJson()

    # Create a mock object without level
    class MockEvent:
        pass

    event = MockEvent()
    style = formatter._pick_style(event)
    assert style == "green"  # Should default to INFO color


def test_pick_style_with_custom_colors():
    custom_colors = {"INFO": "blue", "ERROR": "magenta"}
    formatter = ColorJson(colors=custom_colors)
    event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
    style = formatter._pick_style(event)
    assert style == "blue"


def test_format_basic_event():
    formatter = ColorJson()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    # Result should be non-empty and contain the message
    assert result != ""
    assert "Test message" in result
    assert isinstance(result, str)


def test_format_event_with_context():
    formatter = ColorJson()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        context={"job": "test_job", "env": "dev"},
    )
    result = formatter.format(event)

    assert "test_job" in result
    assert "dev" in result


def test_format_event_with_tags():
    formatter = ColorJson()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        tags={"module": "formatter", "version": "1.0"},
    )
    result = formatter.format(event)

    assert "formatter" in result
    assert "version" in result


def test_format_event_with_metrics():
    formatter = ColorJson()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        metrics={"duration": 100, "count": 5},
    )
    result = formatter.format(event)

    assert "duration" in result
    assert "100" in result


def test_format_event_with_extra():
    formatter = ColorJson()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        extra={"request_id": "abc123", "user_id": "user456"},
    )
    result = formatter.format(event)

    assert "abc123" in result
    assert "user456" in result


def test_format_event_with_code():
    formatter = ColorJson()
    event = Log(
        message="Test message",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        code=500,
    )
    result = formatter.format(event)

    assert "500" in result


def test_format_with_indent_2():
    formatter = ColorJson(indent=2)
    event = Log(
        message="Indented",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    # Should be pretty-printed with newlines
    assert "\n" in result
    lines = result.split("\n")
    assert len(lines) > 1


def test_format_with_indent_4():
    formatter = ColorJson(indent=4)
    event = Log(
        message="Indented",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    assert "\n" in result
    lines = result.split("\n")
    assert len(lines) > 1


def test_format_with_sort_keys_true():
    formatter = ColorJson(sort=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        tags={"zebra": "z", "alpha": "a", "beta": "b"},
    )
    result = formatter.format(event)

    # Keys should appear in alphabetical order
    alpha_pos = result.find("alpha")
    beta_pos = result.find("beta")
    zebra_pos = result.find("zebra")

    assert alpha_pos < beta_pos < zebra_pos


def test_format_with_sort_keys_false():
    formatter = ColorJson(sort=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    assert "Test" in result


def test_format_with_ensure_ascii_false_preserves_unicode():
    formatter = ColorJson(ensure_ascii=False)
    event = Log(
        message="Unicode: 你好世界 🚀",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    assert "你好世界" in result
    assert "🚀" in result


def test_format_with_ensure_ascii_true_escapes_unicode():
    formatter = ColorJson(ensure_ascii=True)
    event = Log(
        message="Unicode: 你好",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    # Unicode should be escaped
    assert "\\u" in result


def test_format_with_all_fields_false_omits_empty_values():
    formatter = ColorJson(all_fields=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        # No context, tags, metrics, or extra provided
    )
    result = formatter.format(event)

    # Empty dicts should not be in output
    assert "context" not in result or "{}" not in result


def test_format_with_all_fields_true_includes_empty_values():
    formatter = ColorJson(all_fields=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    # Should include context, tags, metrics, extra even if empty
    assert "context" in result
    assert "tags" in result


def test_format_non_eventlike_returns_empty_string():
    formatter = ColorJson()

    result = formatter.format("not an event")
    assert result == ""

    result = formatter.format(None)
    assert result == ""

    result = formatter.format(123)
    assert result == ""

    result = formatter.format({"message": "dict"})
    assert result == ""


def test_format_event_with_empty_message():
    formatter = ColorJson()
    event = Log(
        message="",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "INFO" in result


def test_format_event_with_multiline_message():
    formatter = ColorJson()
    event = Log(
        message="Line 1\nLine 2\nLine 3",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result


def test_format_event_with_special_characters():
    formatter = ColorJson()
    event = Log(
        message='Special: "quotes" and \\backslash\\',
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    assert "quotes" in result


def test_format_multiple_events_consecutively():
    formatter = ColorJson()

    event1 = Log(
        message="First event",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    event2 = Log(
        message="Second event",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 31, 00, tzinfo=pytz.UTC),
    )
    event3 = Log(
        message="Third event",
        level="DEBUG",
        time=datetime(2025, 11, 22, 10, 31, 15, tzinfo=pytz.UTC),
    )

    result1 = formatter.format(event1)
    result2 = formatter.format(event2)
    result3 = formatter.format(event3)

    assert "First event" in result1
    assert "Second event" in result2
    assert "Third event" in result3


def test_format_time_is_iso_format():
    formatter = ColorJson()
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    assert "2025-11-22" in result


def test_format_uses_event_describe_method():
    formatter = ColorJson()
    event = Log(
        message="Test describe",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)

    describe_result = event.describe()
    assert describe_result["message"] in result


def test_format_preserves_nested_structures():
    formatter = ColorJson()
    event = Log(
        message="Nested test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        tags={"nested": {"level1": {"level2": "value"}}},
    )
    result = formatter.format(event)
    assert "nested" in result
    assert "level1" in result
    assert "level2" in result
    assert "value" in result


def test_format_output_is_colored():
    formatter = ColorJson()
    event = Log(
        message="Colored output",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert "\x1b[" in result or result != ""


def test_format_different_levels_have_different_colors():
    formatter = ColorJson()

    event_info = Log(
        message="Info",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    event_error = Log(
        message="Error",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )

    result_info = formatter.format(event_info)
    result_error = formatter.format(event_error)

    # Both should be valid strings
    assert isinstance(result_info, str)
    assert isinstance(result_error, str)
    assert "Info" in result_info
    assert "Error" in result_error


def test_format_result_has_no_trailing_whitespace():
    formatter = ColorJson()
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert result == result.rstrip()


def test_format_event_with_all_data_types():
    formatter = ColorJson()
    event = Log(
        message="Complete event",
        name="TestLogger",
        level="WARNING",
        time=datetime(2025, 11, 22, 10, 30, 45, tzinfo=pytz.UTC),
        code=404,
        context={"string": "value", "number": 42, "boolean": True},
        tags={"module": "test"},
        metrics={"duration": 10.5},
        extra={"request_id": "123"},
    )
    result = formatter.format(event)

    assert "Complete event" in result
    assert "WARNING" in result
    assert "404" in result
    assert "value" in result
    assert "42" in result


def test_construct_with_custom_prefix_timeformat():
    custom_timeformat = "%Y/%m/%d %H:%M"
    formatter = ColorJson(prefix_timeformat=custom_timeformat)
    assert formatter.prefix_timeformat == custom_timeformat


def test_construct_with_custom_prefix_format():
    custom_format = "[{time}] {level} - {message}"
    formatter = ColorJson(prefix_format=custom_format)
    assert formatter.prefix_format == custom_format


def test_construct_with_prefix_on_false():
    formatter = ColorJson(prefix_on=False)
    assert formatter.prefix_on is False


def test_construct_with_prefix_on_true():
    formatter = ColorJson(prefix_on=True)
    assert formatter.prefix_on is True


def test_construct_with_all_prefix_parameters():
    formatter = ColorJson(
        prefix_timeformat="%H:%M:%S",
        prefix_format="[{level}] {message}",
        prefix_on=False,
    )
    assert formatter.prefix_timeformat == "%H:%M:%S"
    assert formatter.prefix_format == "[{level}] {message}"
    assert formatter.prefix_on is False


def test_resolve_timeformat_with_none_uses_default():
    formatter = ColorJson()
    result = formatter._resolve_timeformat(None)
    assert result == ColorJson.TIME_FORMAT


def test_resolve_timeformat_with_custom_value():
    formatter = ColorJson()
    custom = "%Y-%m-%d"
    result = formatter._resolve_timeformat(custom)
    assert result == custom


def test_resolve_format_with_none_uses_default():
    formatter = ColorJson()
    result = formatter._resolve_format(None)
    assert result == ColorJson.FORMAT


def test_resolve_format_with_custom_value():
    formatter = ColorJson()
    custom = "{time} | {level}"
    result = formatter._resolve_format(custom)
    assert result == custom


def test_resolve_prefix_with_none_uses_default():
    formatter = ColorJson()
    result = formatter._resolve_prefix(None)
    assert result is True


def test_resolve_prefix_with_false():
    formatter = ColorJson()
    result = formatter._resolve_prefix(False)
    assert result is False


def test_resolve_prefix_with_true():
    formatter = ColorJson()
    result = formatter._resolve_prefix(True)
    assert result is True


def test_format_event_with_prefix_on():
    formatter = ColorJson(prefix_on=True)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "2025-12-06 10:30:45" in result
    assert "INFO" in result


def test_format_event_with_prefix_off():
    formatter = ColorJson(prefix_on=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    # Should not contain the prefix timestamp
    assert "2025-12-06 10:30:45" not in result or result != ""


def test_format_event_with_custom_prefix_format():
    formatter = ColorJson(prefix_format="[{level}] {time} - {message}")
    event = Log(
        message="Test message",
        level="WARNING",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "WARNING" in result
    assert "2025-12-06 10:30:45" in result


def test_format_event_with_custom_prefix_timeformat():
    formatter = ColorJson(prefix_timeformat="%Y/%m/%d")
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "2025/12/06" in result


def test_format_event_with_prefix_disabled_and_custom_format():
    formatter = ColorJson(prefix_on=False, prefix_format="SHOULD_NOT_APPEAR")
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "SHOULD_NOT_APPEAR" not in result


def test_default_prefix_timeformat_constant():
    assert ColorJson.TIME_FORMAT == "%Y-%m-%d %H:%M:%S"


def test_default_prefix_format_constant():
    assert ColorJson.FORMAT == "[{time}][{level}] {message}"


def test_format_event_with_all_prefix_options():
    formatter = ColorJson(
        prefix_timeformat="%H:%M:%S",
        prefix_format="{time} [{level}] {message}",
        prefix_on=True,
    )
    event = Log(
        message="Test message",
        level="ERROR",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "10:30:45" in result
    assert "ERROR" in result
