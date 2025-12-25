from datetime import datetime

import pytz

from xlog.event.base import BaseEvent


def test_init_with_minimal_args():
    event = BaseEvent(message="Test message")
    assert event.message == "Test message"
    assert event.level == "INFO"
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
    event = BaseEvent(
        message="Full event",
        id="event123",
        name="TestEvent",
        time=now,
        tz=pytz.UTC,
        level="WARNING",
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
    assert event.code == 404
    assert event.context == {"user": "alice"}
    assert event.tags == {"env": "prod"}
    assert event.metrics == {"duration": "100ms"}
    assert event.extra == {"custom": "data"}


def test_message_is_stripped():
    event = BaseEvent(message="  Test message  \n")
    assert event.message == "Test message"


def test_empty_message():
    event = BaseEvent(message="")
    assert event.message == ""


def test_none_message():
    event = BaseEvent(message=None)
    assert event.message == ""


def test_level_defaults_to_info():
    event = BaseEvent(message="Test")
    assert event.level == "INFO"


def test_level_is_uppercase():
    event = BaseEvent(message="Test", level="debug")
    assert event.level == "DEBUG"


def test_invalid_level_defaults_to_info():
    event = BaseEvent(message="Test", level="INVALID_LEVEL")
    assert event.level == "INFO"


def test_valid_levels():
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "UNKNOWN"]:
        event = BaseEvent(message="Test", level=level)
        assert event.level == level


def test_code_as_integer():
    event = BaseEvent(message="Test", code=200)
    assert event.code == 200
    assert isinstance(event.code, int)


def test_code_as_string_converts_to_int():
    event = BaseEvent(message="Test", code="404")
    assert event.code == 404
    assert isinstance(event.code, int)


def test_code_invalid_string_returns_none():
    event = BaseEvent(message="Test", code="invalid")
    assert event.code is None


def test_code_none():
    event = BaseEvent(message="Test", code=None)
    assert event.code is None


def test_tz_as_string():
    event = BaseEvent(message="Test", tz="Europe/London")
    assert event.tz == pytz.timezone("Europe/London")
    assert event.tz.zone == "Europe/London"


def test_tz_as_pytz_object():
    tz = pytz.timezone("Asia/Tokyo")
    event = BaseEvent(message="Test", tz=tz)
    assert event.tz.zone == "Asia/Tokyo"
    assert event.tz == tz


def test_tz_invalid_defaults_to_utc():
    event = BaseEvent(message="Test", tz="Invalid/Timezone")
    assert event.tz is None
    assert event.time.tzinfo == pytz.UTC


def test_tz_none_defaults_to_utc():
    event = BaseEvent(message="Test", tz=None)
    assert event.tz is None
    assert event.time.tzinfo == pytz.UTC


def test_time_as_datetime():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = BaseEvent(message="Test", time=now)
    assert event.time == now


def test_time_invalid_string_uses_now():
    event = BaseEvent(message="Test", time="invalid")
    assert isinstance(event.time, datetime)


def test_time_none_uses_now():
    event = BaseEvent(message="Test", time=None)
    assert isinstance(event.time, datetime)


def test_income_aware_datetime():
    time1 = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo"))
    event1 = BaseEvent(message="Test", time=time1)
    assert isinstance(event1.time, datetime)
    assert event1.tz is None
    assert event1.time.tzinfo.zone == "Asia/Tokyo"

    time2 = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.timezone("Australia/Sydney"))
    event2 = BaseEvent(message="Test", time=time2, tz="Australia/Sydney")
    assert isinstance(event2.time, datetime)
    assert event2.tz == pytz.timezone("Australia/Sydney")
    assert event2.tz.zone == "Australia/Sydney"
    assert event2.time.tzinfo.zone == "Australia/Sydney"

    time3 = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event3 = BaseEvent(message="Test", time=time3)
    assert isinstance(event3.time, datetime)
    assert event3.tz is None
    assert event3.time.tzinfo.zone == "UTC"

    time4 = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.FixedOffset(330))
    event4 = BaseEvent(message="Test", time=time4)
    assert isinstance(event4.time, datetime)
    assert event4.tz is None
    assert event4.time.tzinfo.utcoffset(event4.time) == time4.tzinfo.utcoffset(time4)

    time5 = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.FixedOffset(-480))
    event5 = BaseEvent(message="Test", time=time5)
    assert isinstance(event5.time, datetime)
    assert event5.tz is None
    assert event5.time.tzinfo.utcoffset(event5.time) == time5.tzinfo.utcoffset(time5)

    time6 = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai"))
    event6 = BaseEvent(message="Test", time=time6, tz="Asia/Shanghai")
    assert isinstance(event6.time, datetime)
    assert event6.tz == pytz.timezone("Asia/Shanghai")
    assert event6.time.tzinfo.zone == "Asia/Shanghai"


def test_context_serialization():
    event = BaseEvent(
        message="Test",
        context={"timestamp": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.context["timestamp"] == "2023-11-23T10:00:00"


def test_tags_serialization():
    event = BaseEvent(
        message="Test",
        tags={"created": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.tags["created"] == "2023-11-23T10:00:00"


def test_metrics_serialization():
    event = BaseEvent(
        message="Test",
        metrics={"logged": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.metrics["logged"] == "2023-11-23T10:00:00"


def test_extra_serialization():
    event = BaseEvent(
        message="Test",
        extra={"recorded": datetime(2023, 11, 23, 10, 0, 0)},
    )
    assert event.extra["recorded"] == "2023-11-23T10:00:00"


def test_identifier_is_consistent():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = BaseEvent(
        message="Test",
        name="test",
        time=now,
        level="INFO",
        code=200,
    )
    event2 = BaseEvent(
        message="Test",
        name="test",
        time=now,
        level="INFO",
        code=200,
    )
    assert event1.identifier == event2.identifier


def test_identifier_changes_with_different_data():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = BaseEvent(message="Test 1", time=now)
    event2 = BaseEvent(message="Test 2", time=now)
    assert event1.identifier != event2.identifier


def test_equality_with_same_event():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = BaseEvent(message="Test", name="test", time=now)
    event2 = BaseEvent(message="Test", name="test", time=now)
    assert event1 == event2


def test_equality_with_different_event():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = BaseEvent(message="Test 1", time=now)
    event2 = BaseEvent(message="Test 2", time=now)
    assert event1 != event2


def test_equality_with_dict():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = BaseEvent(message="Test", name="test", time=now)
    event_dict = event.to_dict()
    assert event == event_dict


def test_equality_with_identifier_string():
    event = BaseEvent(message="Test")
    assert event == event.identifier


def test_equality_with_other_type():
    event = BaseEvent(message="Test")
    assert event != 123
    assert event != ["list"]
    assert event is not None


def test_not_equal_operator():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event1 = BaseEvent(message="Test 1", time=now)
    event2 = BaseEvent(message="Test 2", time=now)
    assert event1 != event2


def test_get_existing_attribute():
    event = BaseEvent(message="Test", level="WARNING")
    assert event.get("level") == "WARNING"
    assert event.get("message") == "Test"


def test_get_nonexistent_attribute():
    event = BaseEvent(message="Test")
    assert event.get("nonexistent") is None


def test_get_with_default():
    event = BaseEvent(message="Test")
    assert event.get("nonexistent", "default") == "default"


def test_to_dict():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = BaseEvent(
        message="Test",
        id="event123",
        name="test",
        time=now,
        tz="UTC",
        level="INFO",
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
    assert result["code"] == 200
    assert result["context"] == {"key": "value"}
    assert result["tags"] == {"tag": "val"}
    assert result["metrics"] == {"metric": "val"}
    assert result["extra"] == {"extra": "val"}


def test_describe():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    event = BaseEvent(message="Test", time=now)
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
        "level": "ERROR",
        "code": 500,
        "context": {"user": "bob"},
    }
    event = BaseEvent.from_dict(data)
    assert event.id == "event123"
    assert event.message == "Test message"
    assert event.name == "test"
    assert event.level == "ERROR"
    assert event.code == 500
    assert event.context == {"user": "bob"}


def test_from_dict_with_event_object():
    original = BaseEvent(message="Test", level="DEBUG")
    result = BaseEvent.from_dict(original)
    assert result is original


def test_from_dict_with_time_string():
    data = {
        "message": "Test",
        "time": "2023-11-23T12:00:00",
    }
    event = BaseEvent.from_dict(data)
    assert event.time == datetime.fromisoformat("2023-11-23T12:00:00+00:00")


def test_from_dict_with_missing_fields():
    data = {"message": "Test"}
    event = BaseEvent.from_dict(data)
    assert event.message == "Test"
    assert event.level == "INFO"


def test_from_dict_round_trip():
    now = datetime(2023, 11, 23, 12, 0, 0, tzinfo=pytz.UTC)
    original = BaseEvent(
        message="Test",
        name="test",
        time=now,
        level="WARNING",
        code=404,
        context={"key": "value"},
    )
    data = original.to_dict()
    recreated = BaseEvent.from_dict(data)
    assert original == recreated


def test_inherits_from_log_component():
    event = BaseEvent(message="Test")
    assert hasattr(event, "ensure_serialisable")
    assert hasattr(event, "LEVELS")


def test_str_representation():
    event = BaseEvent(message="Test", name="MyEvent")
    assert str(event) == "myevent"


def test_repr_representation():
    event = BaseEvent(message="Test", id="evt123", name="MyEvent")
    result = repr(event)
    assert "BaseEvent" in result
    assert "id=evt123" in result
    assert "name=myevent" in result
