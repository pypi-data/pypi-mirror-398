import json
from datetime import datetime

from xlog.event.logging import Log
from xlog.format.json import Json


def test_construct_with_defaults():
    formatter = Json()
    assert formatter.indent is None
    assert formatter.ensure_ascii is False
    assert formatter.sort is True


def test_construct_with_custom_indent():
    formatter = Json(indent=4)
    assert formatter.indent == 4
    assert formatter.ensure_ascii is False
    assert formatter.sort is True


def test_construct_with_custom_ensure_ascii():
    formatter = Json(ensure_ascii=True)
    assert formatter.indent is None
    assert formatter.ensure_ascii is True
    assert formatter.sort is True


def test_construct_with_custom_sort():
    formatter = Json(sort=False)
    assert formatter.indent is None
    assert formatter.ensure_ascii is False
    assert formatter.sort is False


def test_construct_with_all_custom_parameters():
    formatter = Json(indent=4, ensure_ascii=True, sort=False)
    assert formatter.indent == 4
    assert formatter.ensure_ascii is True
    assert formatter.sort is False


def test_construct_with_none_indent_uses_default():
    formatter = Json(indent=None)
    assert formatter.indent is None


def test_format_basic_event():
    formatter = Json()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["message"] == "Test message"
    assert parsed["level"] == "INFO"
    assert "time" in parsed


def test_format_event_with_context():
    formatter = Json()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        context={"job": "test_job", "env": "dev"},
    )
    result = formatter.format(event)

    parsed = json.loads(result)
    assert parsed["context"]["job"] == "test_job"
    assert parsed["context"]["env"] == "dev"


def test_format_event_with_tags():
    formatter = Json()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        tags={"module": "formatter", "version": "1.0"},
    )
    result = formatter.format(event)

    parsed = json.loads(result)
    assert parsed["tags"]["module"] == "formatter"
    assert parsed["tags"]["version"] == "1.0"


def test_format_event_with_metrics():
    formatter = Json()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        metrics={"duration": 100, "count": 5},
    )
    result = formatter.format(event)

    parsed = json.loads(result)
    assert parsed["metrics"]["duration"] == 100
    assert parsed["metrics"]["count"] == 5


def test_format_event_with_extra():
    formatter = Json()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        extra={"request_id": "abc123", "user_id": "user456"},
    )
    result = formatter.format(event)

    parsed = json.loads(result)
    assert parsed["extra"]["request_id"] == "abc123"
    assert parsed["extra"]["user_id"] == "user456"


def test_format_event_with_code():
    formatter = Json()
    event = Log(
        message="Test message",
        level="ERROR",
        time=datetime(2025, 11, 22, 10, 30, 45),
        code=500,
    )
    result = formatter.format(event)

    parsed = json.loads(result)
    assert parsed["code"] == 500


def test_format_event_with_all_fields():
    formatter = Json()
    event = Log(
        message="Complete event",
        name="TestLogger",
        level="WARNING",
        time=datetime(2025, 11, 22, 10, 30, 45),
        code=404,
        context={"job": "test"},
        tags={"module": "test"},
        metrics={"duration": 10},
        extra={"request_id": "123"},
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["message"] == "Complete event"
    assert parsed["level"] == "WARNING"
    assert parsed["code"] == 404
    assert parsed["context"]["job"] == "test"
    assert parsed["tags"]["module"] == "test"
    assert parsed["metrics"]["duration"] == 10
    assert parsed["extra"]["request_id"] == "123"


def test_format_with_indent_2():
    formatter = Json(indent=2)
    event = Log(
        message="Indented",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)

    # Should be pretty-printed with 2-space indent
    assert "\n" in result
    lines = result.split("\n")
    assert len(lines) > 1


def test_format_with_indent_4():
    formatter = Json(indent=4)
    event = Log(
        message="Indented",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "\n" in result

    lines = result.split("\n")
    assert len(lines) > 1

    indented_lines = [line for line in lines if line.startswith("    ")]
    assert len(indented_lines) > 0


def test_format_with_indent_none_compacts():
    formatter = Json(indent=None)
    event = Log(
        message="Compact",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["message"] == "Compact"


def test_format_with_sort_keys_true():
    formatter = Json(sort=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        tags={"zebra": "z", "alpha": "a", "beta": "b"},
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    tag_keys = list(parsed["tags"].keys())
    assert tag_keys == ["alpha", "beta", "zebra"]


def test_format_with_sort_keys_false():
    formatter = Json(sort=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["message"] == "Test"


def test_format_with_ensure_ascii_false_preserves_unicode():
    formatter = Json(ensure_ascii=False)
    event = Log(
        message="Unicode: 你好世界 🚀",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "你好世界" in result
    assert "🚀" in result

    parsed = json.loads(result)
    assert parsed["message"] == "Unicode: 你好世界 🚀"


def test_format_with_ensure_ascii_true_escapes_unicode():
    formatter = Json(ensure_ascii=True)
    event = Log(
        message="Unicode: 你好",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    assert "\\u" in result

    parsed = json.loads(result)
    assert parsed["message"] == "Unicode: 你好"


def test_format_non_Log_returns_empty_string():
    formatter = Json()
    result = formatter.format("not a log event")
    assert result == ""

    result = formatter.format(None)
    assert result == ""

    result = formatter.format(123)
    assert result == ""

    result = formatter.format({"message": "dict"})
    assert result == ""


def test_format_event_with_empty_message():
    formatter = Json()
    event = Log(
        message="",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        all_fields=True,
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["level"] == "INFO"


def test_format_event_with_multiline_message():
    formatter = Json()
    event = Log(
        message="Line 1\nLine 2\nLine 3",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["message"] == "Line 1\nLine 2\nLine 3"
    assert "\n" in parsed["message"]


def test_format_event_with_special_characters():
    formatter = Json()
    event = Log(
        message='Special: "quotes" and \\backslash\\',
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert '"quotes"' in parsed["message"]
    assert "\\" in parsed["message"]


def test_format_multiple_events_consecutively():
    formatter = Json()
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
    parsed1 = json.loads(result1)
    parsed2 = json.loads(result2)
    parsed3 = json.loads(result3)
    assert parsed1["message"] == "First event"
    assert parsed1["level"] == "INFO"
    assert parsed2["message"] == "Second event"
    assert parsed2["level"] == "ERROR"
    assert parsed3["message"] == "Third event"
    assert parsed3["level"] == "DEBUG"


def test_format_result_is_valid_json():
    formatter = Json()
    event = Log(
        message="Validity test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_format_time_is_iso_format():
    formatter = Json()
    event = Log(
        message="Test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)

    parsed = json.loads(result)
    assert "time" in parsed
    assert isinstance(parsed["time"], str)
    datetime.fromisoformat(parsed["time"])


def test_format_uses_event_describe_method():
    formatter = Json()
    event = Log(
        message="Test describe",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    describe_result = event.describe()
    assert parsed["message"] == describe_result["message"]
    assert parsed["level"] == describe_result["level"]


def test_format_event_with_long_message():
    formatter = Json()
    long_message = "x" * 1000
    event = Log(
        message=long_message,
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["message"] == long_message
    assert len(parsed["message"]) == 1000


def test_format_preserves_nested_structures():
    formatter = Json()
    event = Log(
        message="Nested test",
        level="INFO",
        time=datetime(2025, 11, 22, 10, 30, 45),
        tags={"nested": {"level1": {"level2": "value"}}},
    )
    result = formatter.format(event)
    parsed = json.loads(result)
    assert parsed["tags"]["nested"]["level1"]["level2"] == "value"
