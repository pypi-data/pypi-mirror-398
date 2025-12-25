import logging
from datetime import datetime

import pytz

from xlog.event.logging import Log


def test_init_with_minimal_args():
    event = Log(message="Test message")
    assert event.message == "Test message"
    assert event.level == "INFO"
    assert event.levelno == logging.INFO
    assert event.tz is None
    assert event.code is None
    assert event.context == {}
    assert event.tags == {}
    assert event.metrics == {}
    assert event.extra == {}
    assert len(event.id) == 10
    assert len(event.identifier) == 12


def test_init_with_all_args():
    now = datetime(2023, 11, 23, 15, 30, 45, tzinfo=pytz.UTC)
    event = Log(
        message="Full event",
        id="event123",
        name="TestEvent",
        time=now,
        tz=pytz.UTC,
        level=logging.WARNING,
        code=404,
        context={"user": "alice"},
        tags={"env": "prod"},
        metrics={"duration": "100ms"},
        extra={"custom": "data"},
    )
    assert event.message == "Full event"
    assert event.id == "event123"
    assert event.name == "testevent"
    assert event.time.isoformat() == now.isoformat()
    assert event.tz == pytz.UTC
    assert event.level == "WARNING"
    assert event.levelno == logging.WARNING
    assert event.code == 404
    assert event.context == {"user": "alice"}
    assert event.tags == {"env": "prod"}
    assert event.metrics == {"duration": "100ms"}
    assert event.extra == {"custom": "data"}


def test_message_is_stripped():
    event = Log(message="  Test message  \n")
    assert event.message == "Test message"


def test_empty_message():
    event = Log(message="")
    assert event.message == ""


def test_none_message():
    event = Log(message=None)
    assert event.message == ""


def test_level_defaults_to_info():
    event = Log(message="Test")
    assert event.level == "INFO"
    assert event.levelno == logging.INFO


def test_level_is_uppercase():
    event = Log(message="Test", level="debug")
    assert event.level == "DEBUG"
    assert event.levelno == logging.DEBUG


def test_invalid_level_defaults_to_info():
    event = Log(message="Test", level="INVALID_LEVEL")
    assert event.level == "INFO"
    assert event.levelno == logging.INFO


def test_valid_levels():
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "UNKNOWN"]:
        event = Log(message="Test", level=level)
        assert event.level == level
        assert event.levelno == getattr(logging, level, logging.INFO)


def test_code_as_integer():
    event = Log(message="Test", code=200)
    assert event.code == 200
    assert isinstance(event.code, int)


def test_code_as_string_converts_to_int():
    event = Log(message="Test", code="404")
    assert event.code == 404
    assert isinstance(event.code, int)


def test_code_invalid_string_returns_none():
    event = Log(message="Test", code="invalid")
    assert event.code is None


def test_code_none():
    event = Log(message="Test", code=None)
    assert event.code is None


def test_tz_as_string():
    event = Log(message="Test", tz="Europe/London")
    assert event.tz == pytz.timezone("Europe/London")


def test_tz_as_pytz_object():
    tz = pytz.timezone("Asia/Tokyo")
    event = Log(message="Test", tz=tz)
    assert event.tz == pytz.timezone("Asia/Tokyo")


def test_tz_invalid_defaults_to_utc():
    event = Log(message="Test", tz="Invalid/Timezone")
    assert event.tz is None
    assert event.time.tzinfo == pytz.UTC


def test_tz_none_defaults_to_utc():
    event = Log(message="Test", tz=None)
    assert event.tz is None
    assert event.time.tzinfo == pytz.UTC


def test_time_as_datetime():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = Log(message="Test", time=now)
    assert event.time == now


def test_time_as_iso_string():
    time_str = "2023-11-23T12:00:00"
    event = Log(message="Test", time=time_str)
    expected = datetime.fromisoformat(time_str)
    assert event.time.replace(tzinfo=None) == expected


def test_time_invalid_string_uses_now():
    event = Log(message="Test", time="invalid")
    assert isinstance(event.time, datetime)


def test_time_none_uses_now():
    event = Log(message="Test", time=None)
    assert isinstance(event.time, datetime)


def test_context_serialization():
    event = Log(
        message="Test",
        context={"timestamp": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.context["timestamp"] == "2023-11-23T10:00:00"


def test_tags_serialization():
    event = Log(
        message="Test",
        tags={"created": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.tags["created"] == "2023-11-23T10:00:00"


def test_metrics_serialization():
    event = Log(
        message="Test",
        metrics={"logged": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.metrics["logged"] == "2023-11-23T10:00:00"


def test_extra_serialization():
    event = Log(
        message="Test",
        extra={"recorded": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.extra["recorded"] == "2023-11-23T10:00:00"


def test_identifier_is_consistent():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = Log(
        message="Test",
        name="test",
        time=now,
        level="INFO",
        code=200,
    )
    event2 = Log(
        message="Test",
        name="test",
        time=now,
        level="INFO",
        code=200,
    )
    assert event1.identifier == event2.identifier


def test_identifier_changes_with_different_data():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = Log(message="Test 1", time=now)
    event2 = Log(message="Test 2", time=now)
    assert event1.identifier != event2.identifier


def test_equality_with_same_event():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = Log(message="Test", name="test", time=now)
    event2 = Log(message="Test", name="test", time=now)
    assert event1 == event2


def test_equality_with_different_event():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = Log(message="Test 1", time=now)
    event2 = Log(message="Test 2", time=now)
    assert event1 != event2


def test_equality_with_dict():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = Log(message="Test", name="test", time=now)
    event_dict = event.to_dict()
    assert event == event_dict


def test_equality_with_identifier_string():
    event = Log(message="Test")
    assert event == event.identifier


def test_equality_with_other_type():
    event = Log(message="Test")
    assert event != 123
    assert event != ["list"]
    assert event is not None


def test_not_equal_operator():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = Log(message="Test 1", time=now)
    event2 = Log(message="Test 2", time=now)
    assert event1 != event2


def test_get_existing_attribute():
    event = Log(message="Test", level="WARNING")
    assert event.get("level") == "WARNING"
    assert event.get("levelno") == logging.WARNING
    assert event.get("message") == "Test"


def test_get_nonexistent_attribute():
    event = Log(message="Test")
    assert event.get("nonexistent") is None


def test_get_with_default():
    event = Log(message="Test")
    assert event.get("nonexistent", "default") == "default"


def test_to_dict():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = Log(
        message="Test",
        id="event123",
        name="test",
        time=now,
        tz=pytz.UTC,
        level=logging.INFO,
        code=200,
        context={"key": "value"},
        tags={"tag": "val"},
        metrics={"metric": "val"},
        extra={"extra": "val"},
    )
    result = event.to_dict()
    assert result["id"] == "event123"
    assert result["name"] == "test"
    assert result["message"] == "Test"
    assert result["time"] == now.isoformat()
    assert result["tz"] == "UTC"
    assert result["level"] == "INFO"
    assert result["levelno"] == logging.INFO
    assert result["code"] == 200
    assert result["context"] == {"key": "value"}
    assert result["tags"] == {"tag": "val"}
    assert result["metrics"] == {"metric": "val"}
    assert result["extra"] == {"extra": "val"}


def test_describe():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = Log(message="Test", time=now)
    result = event.describe()
    assert isinstance(result, dict)
    assert result["message"] == "Test"
    assert result["time"] == "2023-11-23T12:00:00+00:00"
    assert result["level"] == "INFO"


def test_from_dict_with_dict():
    data = {
        "id": "event123",
        "message": "Test message",
        "name": "test",
        "level": logging.ERROR,
        "code": 500,
        "context": {"user": "bob"},
    }
    event = Log.from_dict(data)
    assert event.id == "event123"
    assert event.message == "Test message"
    assert event.name == "test"
    assert event.level == "ERROR"
    assert event.levelno == logging.ERROR
    assert event.code == 500
    assert event.context == {"user": "bob"}


def test_from_dict_with_event_object():
    original = Log(message="Test", level="DEBUG")
    result = Log.from_dict(original)
    assert result is original


def test_from_dict_with_time_string():
    data = {
        "message": "Test",
        "time": "2023-11-23T12:00:00",
    }
    event = Log.from_dict(data)
    expected = datetime.fromisoformat("2023-11-23T12:00:00")
    assert event.time.replace(tzinfo=None) == expected


def test_from_dict_with_missing_fields():
    data = {"message": "Test"}
    event = Log.from_dict(data)
    assert event.message == "Test"
    assert event.level == "INFO"
    assert event.levelno == logging.INFO


def test_from_dict_round_trip():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    original = Log(
        message="Test",
        name="test",
        time=now,
        level="WARNING",
        code=404,
        context={"key": "value"},
    )
    data = original.to_dict()
    recreated = Log.from_dict(data)
    assert original == recreated


def test_inherits_from_base_event():
    event = Log(message="Test")
    assert hasattr(event, "ensure_serialisable")
    assert hasattr(event, "LEVELS")
    assert hasattr(event, "_resolve_level")
    assert hasattr(event, "_resolve_message")


def test_str_representation():
    event = Log(message="This is my message")
    assert str(event) == "This is my message"


def test_str_with_empty_message():
    event = Log(message="")
    assert str(event) == ""


def test_repr_representation():
    event = Log(message="Test message", level="ERROR")
    result = repr(event)
    assert "Log" in result
    assert "message=Test message" in result
    assert "level=ERROR" in result


def test_repr_with_info_level():
    event = Log(message="Info message")
    result = repr(event)
    assert "Log" in result
    assert "message=Info message" in result
    assert "level=INFO" in result


def test_kwargs_are_passed_to_parent():
    event = Log(message="Test", custom_kwarg="value")
    assert event.message == "Test"


def test_multiple_events_have_unique_ids():
    event1 = Log(message="Event 1")
    event2 = Log(message="Event 2")
    event3 = Log(message="Event 3")

    assert event1.id != event2.id
    assert event2.id != event3.id
    assert event1.id != event3.id


def test_multiple_events_have_unique_identifiers():
    event1 = Log(message="Event 1")
    event2 = Log(message="Event 2")
    event3 = Log(message="Event 3")

    assert event1.identifier != event2.identifier
    assert event2.identifier != event3.identifier
    assert event1.identifier != event3.identifier


def test_log_event_with_context():
    event = Log(
        message="User login",
        level=logging.INFO,
        context={
            "user_id": "12345",
            "ip_address": "192.168.1.1",
            "timestamp": datetime(2023, 11, 23, 10, 0, 0),
        },
    )
    assert event.message == "User login"
    assert event.context["user_id"] == "12345"
    assert event.context["ip_address"] == "192.168.1.1"
    assert event.context["timestamp"] == "2023-11-23T10:00:00"


def test_log_event_with_tags():
    event = Log(
        message="Database query",
        tags={
            "service": "api",
            "environment": "production",
            "version": "1.2.3",
        },
    )
    assert event.tags["service"] == "api"
    assert event.tags["environment"] == "production"
    assert event.tags["version"] == "1.2.3"


def test_log_event_with_metrics():
    event = Log(
        message="Request completed",
        metrics={
            "duration_ms": "150",
            "memory_mb": "256",
            "cpu_percent": "45.5",
        },
    )
    assert event.metrics["duration_ms"] == "150"
    assert event.metrics["memory_mb"] == "256"
    assert event.metrics["cpu_percent"] == "45.5"


def test_log_event_error_with_code():
    event = Log(
        message="Database connection failed",
        level="ERROR",
        code=500,
        context={"error": "Connection timeout"},
    )
    assert event.message == "Database connection failed"
    assert event.level == "ERROR"
    assert event.code == 500
    assert event.context["error"] == "Connection timeout"


def test_log_event_debug_message():
    event = Log(
        message="Debug information",
        level="DEBUG",
        extra={"stack_trace": "line 1\nline 2\nline 3"},
    )
    assert event.level == "DEBUG"
    assert event.levelno == logging.DEBUG
    assert event.message == "Debug information"
    assert event.extra["stack_trace"] == "line 1\nline 2\nline 3"
