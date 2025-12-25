from collections import deque
from datetime import datetime

import pytz

from xlog.event.base import BaseEvent
from xlog.event.logging import Log
from xlog.format.json import Json
from xlog.group.loggroup import LogGroup
from xlog.node.logging import Logging
from xlog.stream.stream import LogStream


def test_init_with_defaults():
    stream = LogStream()
    assert stream.level == "INFO"
    assert stream.verbose is False
    assert isinstance(stream.format, Json)
    assert isinstance(stream.node, Logging)
    assert stream.local is False
    assert stream.max_local == 10_000
    assert len(stream.groups) == 0
    assert len(stream.events) == 0
    assert stream.event_count == 0
    assert len(stream.id) == 10


def test_init_with_custom_parameters():
    stream = LogStream(
        id="stream123",
        name="TestStream",
        level="DEBUG",
        verbose=True,
        local=True,
        max_local=5000,
    )
    assert stream.id == "stream123"
    assert stream.name == "teststream"
    assert stream.level == "DEBUG"
    assert stream.verbose is True
    assert stream.local is True
    assert stream.max_local == 5000
    assert stream.events.maxlen == 5000


def test_init_with_custom_format():
    custom_format = Json()
    stream = LogStream(format=custom_format)
    assert stream.format is custom_format


def test_init_with_custom_node():
    custom_node = Logging(name="custom", level="ERROR")
    stream = LogStream(node=custom_node)
    assert stream.node is custom_node


def test_init_with_groups():
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream = LogStream(groups=[group1, group2])
    assert len(stream.groups) == 2
    assert group1 in stream.groups
    assert group2 in stream.groups
    group1.close()
    group2.close()


def test_init_with_events():
    event1 = Log(
        message="Event 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Event 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    stream = LogStream(
        local=True,
        events=deque([event1, event2]),
    )
    assert len(stream.events) == 2
    assert stream.event_count == 2


def test_init_with_events_non_local():
    event1 = Log(
        message="Event 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Event 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    stream = LogStream(
        local=False,
        events=deque([event1, event2]),
    )
    assert len(stream.events) == 0
    assert stream.event_count == 2


def test_resolve_verbose_none():
    stream = LogStream(verbose=None)
    assert stream.verbose is False


def test_resolve_verbose_true():
    stream = LogStream(verbose=True)
    assert stream.verbose is True


def test_resolve_verbose_false():
    stream = LogStream(verbose=False)
    assert stream.verbose is False


def test_resolve_format_default():
    stream = LogStream()
    assert isinstance(stream.format, Json)


def test_resolve_format_custom():
    custom_format = Json()
    stream = LogStream(format=custom_format)
    assert stream.format is custom_format


def test_resolve_node_default():
    stream = LogStream(name="TestNode", level="DEBUG", verbose=True)
    assert isinstance(stream.node, Logging)
    assert stream.node.name == "testnode"


def test_resolve_node_custom():
    custom_node = Logging(name="custom")
    stream = LogStream(node=custom_node)
    assert stream.node is custom_node


def test_resolve_local_none():
    stream = LogStream(local=None)
    assert stream.local is False


def test_resolve_local_true():
    stream = LogStream(local=True)
    assert stream.local is True


def test_resolve_local_false():
    stream = LogStream(local=False)
    assert stream.local is False


def test_resolve_max_local_default():
    stream = LogStream()
    assert stream.max_local == 10_000


def test_resolve_max_local_custom():
    stream = LogStream(max_local=5000)
    assert stream.max_local == 5000


def test_resolve_max_local_zero():
    stream = LogStream(max_local=0)
    assert stream.max_local == 10_000


def test_resolve_max_local_negative():
    stream = LogStream(max_local=-100)
    assert stream.max_local == 10_000


def test_resolve_events_local_true():
    stream = LogStream(local=True, max_local=100)
    assert stream.events.maxlen == 100


def test_resolve_events_local_false():
    stream = LogStream(local=False)
    assert stream.events.maxlen is None


def test_resolve_events_with_dict():
    event_dict = {
        "message": "Test",
        "level": "INFO",
        "time": datetime.now(pytz.UTC).isoformat(),
    }
    stream = LogStream(local=True, events=deque([event_dict]))
    assert len(stream.events) == 1


def test_resolve_groups_empty():
    stream = LogStream(groups=None)
    assert len(stream.groups) == 0
    assert isinstance(stream.groups, list)


def test_resolve_groups_with_valid_groups():
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream = LogStream(groups=[group1, group2])
    assert len(stream.groups) == 2
    group1.close()
    group2.close()


def test_resolve_groups_filters_invalid():
    group = LogGroup(name="valid")
    stream = LogStream(groups=[group, "invalid", 123])
    assert len(stream.groups) == 1
    assert stream.groups[0] is group
    group.close()


def test_event_method():
    stream = LogStream(local=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    returned_event = stream.event(event)
    assert returned_event is event
    assert len(stream.events) == 1
    assert stream.event_count == 1


def test_event_method_non_local():
    stream = LogStream(local=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    returned_event = stream.event(event)
    assert returned_event is event
    assert len(stream.events) == 0
    assert stream.event_count == 1


def test_log_method():
    stream = LogStream(local=True)
    event = stream.log("Test message", level="DEBUG")
    assert isinstance(event, BaseEvent)
    assert event.message == "Test message"
    assert len(stream.events) == 1
    assert stream.event_count == 1


def test_log_method_with_kwargs():
    stream = LogStream(local=True)
    event = stream.log(
        "Test message",
        level="ERROR",
        code=500,
        context={"user": "test"},
    )
    assert event.message == "Test message"
    assert event.level == "ERROR"
    assert event.code == 500
    assert stream.event_count == 1


def test_add_event_increments_count():
    stream = LogStream(local=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._add_event(event)
    assert stream.event_count == 1
    stream._add_event(event)
    assert stream.event_count == 2


def test_add_event_with_groups():
    group = LogGroup(name="testgroup")
    stream = LogStream(name="TestStream", groups=[group], local=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._add_event(event)
    assert stream.event_count == 1
    events = group.list_events("teststream")
    assert len(events) == 1
    group.close()


def test_add_event_with_multiple_groups():
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream = LogStream(name="TestStream", groups=[group1, group2], local=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._add_event(event)
    assert len(group1.list_events("teststream")) == 1
    assert len(group2.list_events("teststream")) == 1
    group1.close()
    group2.close()


def test_add_event_group_exception_continues():
    class FailingGroup:
        def receive(self, stream, event):
            raise Exception("Group error")

        def to_dict(self):
            return {}

    failing_group = FailingGroup()
    working_group = LogGroup(name="working")
    stream = LogStream(groups=[failing_group, working_group], local=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._add_event(event)
    assert stream.event_count == 1
    working_group.close()


def test_add_event_local_storage():
    stream = LogStream(local=True, max_local=3)
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        stream._add_event(event)
    assert stream.event_count == 5
    assert len(stream.events) == 3


def test_log_with_node():
    stream = LogStream(local=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._log(event)


def test_log_with_custom_level():
    stream = LogStream(level="DEBUG", local=False)
    event = Log(
        message="Test",
        time=datetime.now(pytz.UTC),
    )
    stream._log(event)


def test_log_with_invalid_node():
    stream = LogStream(local=False)
    stream.node = "invalid"
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._log(event)


def test_log_node_exception_handled():
    class FailingNode:
        def log(self, level, message):
            raise Exception("Node error")

    stream = LogStream(local=False)
    stream.node = FailingNode()
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream._log(event)


def test_add_group():
    stream = LogStream()
    group = LogGroup(name="newgroup")
    stream.add_group(group)
    assert group in stream.groups
    assert len(stream.groups) == 1
    group.close()


def test_add_group_duplicate():
    group = LogGroup(name="testgroup")
    stream = LogStream(groups=[group])
    stream.add_group(group)
    assert len(stream.groups) == 1
    group.close()


def test_add_group_multiple():
    stream = LogStream()
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream.add_group(group1)
    stream.add_group(group2)
    assert len(stream.groups) == 2
    group1.close()
    group2.close()


def test_remove_group():
    group = LogGroup(name="testgroup")
    stream = LogStream(groups=[group])
    stream.remove_group(group)
    assert len(stream.groups) == 0
    group.close()


def test_remove_group_not_present():
    group = LogGroup(name="testgroup")
    stream = LogStream()
    stream.remove_group(group)
    assert len(stream.groups) == 0
    group.close()


def test_remove_group_from_multiple():
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream = LogStream(groups=[group1, group2])
    stream.remove_group(group1)
    assert len(stream.groups) == 1
    assert group2 in stream.groups
    group1.close()
    group2.close()


def test_list_events_empty():
    stream = LogStream(local=True)
    events = stream.list_events()
    assert isinstance(events, list)
    assert len(events) == 0


def test_list_events_with_events():
    stream = LogStream(local=True)
    event1 = Log(
        message="Event 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Event 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    stream.event(event1)
    stream.event(event2)
    events = stream.list_events()
    assert len(events) == 2
    assert events[0] is event1
    assert events[1] is event2


def test_list_events_returns_copy():
    stream = LogStream(local=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream.event(event)
    events1 = stream.list_events()
    events2 = stream.list_events()
    assert events1 is not events2
    assert events1[0] is events2[0]


def test_describe_returns_dict():
    stream = LogStream(
        id="test123",
        name="TestStream",
        level="DEBUG",
        verbose=True,
        local=True,
        max_local=5000,
    )
    result = stream.describe()
    assert isinstance(result, dict)
    assert result["id"] == "test123"
    assert result["name"] == "teststream"
    assert result["level"] == "DEBUG"
    assert result["verbose"] is True
    assert result["local"] is True
    assert result["max_local"] == 5000
    assert result["event_count"] == 0
    assert isinstance(result["events"], list)
    assert isinstance(result["groups"], list)


def test_describe_with_events():
    stream = LogStream(local=True)
    event1 = Log(
        message="Event 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Event 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    stream.event(event1)
    stream.event(event2)
    result = stream.describe()
    assert len(result["events"]) == 2
    assert result["events"][0] == "Event 1"
    assert result["events"][1] == "Event 2"


def test_describe_with_groups():
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream = LogStream(groups=[group1, group2])
    result = stream.describe()
    assert len(result["groups"]) == 2
    assert "group1" in result["groups"]
    assert "group2" in result["groups"]
    group1.close()
    group2.close()


def test_to_dict_returns_dict():
    stream = LogStream(
        id="test456",
        name="DictTest",
        level="ERROR",
        verbose=False,
        local=False,
        max_local=1000,
    )
    result = stream.to_dict()
    assert isinstance(result, dict)
    assert result["id"] == "test456"
    assert result["name"] == "dicttest"
    assert result["level"] == "ERROR"
    assert result["verbose"] is False
    assert result["local"] is False
    assert result["max_local"] == 1000


def test_to_dict_with_events():
    stream = LogStream(local=True)
    event1 = Log(
        message="Event 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Event 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    stream.event(event1)
    stream.event(event2)
    result = stream.to_dict()
    assert len(result["events"]) == 2
    assert isinstance(result["events"][0], dict)
    assert result["events"][0]["message"] == "Event 1"
    assert result["events"][1]["message"] == "Event 2"


def test_to_dict_with_groups():
    group1 = LogGroup(name="group1")
    group2 = LogGroup(name="group2")
    stream = LogStream(groups=[group1, group2])
    result = stream.to_dict()
    assert len(result["groups"]) == 2
    assert isinstance(result["groups"][0], dict)
    assert isinstance(result["groups"][1], dict)
    group1.close()
    group2.close()


def test_inherits_from_log_component():
    stream = LogStream()
    assert hasattr(stream, "id")
    assert hasattr(stream, "name")
    assert hasattr(stream, "describe")
    assert hasattr(stream, "to_dict")


def test_event_count_persists():
    stream = LogStream(local=False)
    for i in range(10):
        stream.log(f"Message {i}")
    assert stream.event_count == 10
    assert len(stream.events) == 0


def test_local_maxlen_enforcement():
    stream = LogStream(local=True, max_local=5)
    for i in range(10):
        stream.log(f"Message {i}")
    assert stream.event_count == 10
    assert len(stream.events) == 5


def test_multiple_streams_to_same_group():
    group = LogGroup(name="shared")
    stream1 = LogStream(name="Stream1", groups=[group])
    stream2 = LogStream(name="Stream2", groups=[group])
    stream1.log("From stream 1")
    stream2.log("From stream 2")
    streams = group.list_streams()
    assert "stream1" in streams
    assert "stream2" in streams
    group.close()


def test_event_ordering_preserved():
    stream = LogStream(local=True, max_local=10)
    events = []
    for i in range(5):
        event = stream.log(f"Message {i}")
        events.append(event)
    stored = stream.list_events()
    for i, stored_event in enumerate(stored):
        assert stored_event.message == f"Message {i}"


def test_full_lifecycle():
    group = LogGroup(name="lifecycle")
    stream = LogStream(
        name="LifecycleStream",
        level="INFO",
        local=True,
        groups=[group],
    )
    for i in range(3):
        stream.log(f"Event {i}", level="INFO")
    assert stream.event_count == 3
    assert len(stream.events) == 3
    assert len(group.list_events("lifecyclestream")) == 3
    result = stream.describe()
    assert result["event_count"] == 3
    dict_result = stream.to_dict()
    assert len(dict_result["events"]) == 3
    group.close()


def test_name_normalization():
    stream = LogStream(name="MyTestStream")
    assert stream.name == "myteststream"


def test_id_auto_generation():
    stream1 = LogStream()
    stream2 = LogStream()
    assert len(stream1.id) == 10
    assert len(stream2.id) == 10
    assert stream1.id != stream2.id


def test_verbose_converts_to_bool():
    stream1 = LogStream(verbose=1)
    assert stream1.verbose is True
    stream2 = LogStream(verbose=0)
    assert stream2.verbose is False


def test_local_converts_to_bool():
    stream1 = LogStream(local=1)
    assert stream1.local is True
    stream2 = LogStream(local=0)
    assert stream2.local is False


def test_max_local_converts_to_int():
    stream = LogStream(max_local=500.7)
    assert stream.max_local == 500
    assert isinstance(stream.max_local, int)


def test_events_deque_type():
    stream = LogStream(local=True)
    assert isinstance(stream.events, deque)


def test_groups_list_type():
    stream = LogStream()
    assert isinstance(stream.groups, list)


def test_event_with_no_level_uses_stream_level():
    stream = LogStream(level="WARNING", local=True)
    event = BaseEvent(message="Test")
    stream.event(event)


def test_log_uses_event_level_over_stream_level():
    stream = LogStream(level="INFO", local=False)
    event = Log(
        message="Test",
        level="ERROR",
        time=datetime.now(pytz.UTC),
    )
    stream._log(event)
