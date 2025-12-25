from datetime import datetime

import pytz

from xlog.event.logging import Log
from xlog.group.loggroup import LogGroup


def test_init_with_defaults():
    group = LogGroup()
    assert group.store is True
    assert group._async is False
    assert group.max_len is None
    assert len(group.id) == 10
    group.close()


def test_init_with_custom_parameters():
    group = LogGroup(
        id="test123",
        name="TestGroup",
        async_=True,
        max_queue=500,
        max_len=1000,
    )
    assert group.id == "test123"
    assert group.name == "testgroup"
    assert group._async is True
    assert group.max_len == 1000
    group.close(timeout=1.0)


def test_init_with_none_max_len():
    group = LogGroup(max_len=None)
    assert group.max_len is None
    group.close()


def test_sync_mode_initialization():
    group = LogGroup(async_=False)
    assert group._async is False
    assert group._queue is None
    assert group._worker is None
    group.close()


def test_async_mode_initialization():
    group = LogGroup(async_=True)
    assert group._async is True
    assert group._queue is not None
    assert group._worker is not None
    assert group._worker.is_alive()
    group.close(timeout=1.0)


def test_sync_receive_event():
    group = LogGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    assert "stream1" in group._events
    assert len(group._events["stream1"]) == 1
    group.close()


def test_sync_receive_multiple_events():
    group = LogGroup(async_=False)
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
    event3 = Log(
        message="Event 3",
        level="ERROR",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream2", event2)
    group.receive("stream1", event3)
    assert len(group._events["stream1"]) == 2
    assert len(group._events["stream2"]) == 1
    group.close()


def test_async_receive_event():
    group = LogGroup(async_=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    assert "stream1" in group._events
    assert len(group._events["stream1"]) == 1
    group.close(timeout=1.0)


def test_async_receive_multiple_events():
    group = LogGroup(async_=True)
    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    group.flush()
    assert len(group._events["stream1"]) == 10
    group.close(timeout=1.0)


def test_store_true_saves_events():
    group = LogGroup(async_=False)
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
    group.receive("stream1", event1)
    group.receive("stream1", event2)
    assert "stream1" in group._events
    assert len(group._events["stream1"]) == 2
    group.close()


def test_store_save_events():
    group = LogGroup(async_=False)
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
    group.receive("stream1", event1)
    group.receive("stream1", event2)
    assert len(group._events.get("stream1", [])) == 2
    group.close()


def test_max_len_limits_stored_events():
    group = LogGroup(async_=False, max_len=3)
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    assert len(group._events["stream1"]) == 3
    stored = list(group._events["stream1"])
    assert stored[0].message == "Event 2"
    assert stored[1].message == "Event 3"
    assert stored[2].message == "Event 4"
    group.close()


def test_list_streams_empty():
    group = LogGroup(async_=False)
    assert group.list_streams() == []
    group.close()


def test_list_streams_with_events():
    group = LogGroup(async_=False)
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
    group.receive("stream1", event1)
    group.receive("stream2", event2)
    group.receive("stream3", event1)
    streams = group.list_streams()
    assert len(streams) == 3
    assert "stream1" in streams
    assert "stream2" in streams
    assert "stream3" in streams
    group.close()


def test_list_events_empty():
    group = LogGroup(async_=False)
    assert group.list_events() == []
    group.close()


def test_list_events_all():
    group = LogGroup(async_=False)
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
    event3 = Log(
        message="Event 3",
        level="ERROR",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream2", event2)
    group.receive("stream1", event3)
    events = group.list_events()
    assert len(events) == 3
    assert event1 in events
    assert event2 in events
    assert event3 in events
    group.close()


def test_list_events_by_stream():
    group = LogGroup(async_=False)
    event1 = Log(
        message="Stream1 Event",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Stream2 Event",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream2", event2)
    stream1_events = group.list_events("stream1")
    assert len(stream1_events) == 1
    assert event1 in stream1_events
    stream2_events = group.list_events("stream2")
    assert len(stream2_events) == 1
    assert event2 in stream2_events
    group.close()


def test_describe_returns_dict():
    group = LogGroup(
        id="test123",
        name="TestGroup",
        async_=False,
    )
    result = group.describe()
    assert isinstance(result, dict)
    assert result["id"] == "test123"
    assert result["name"] == "testgroup"
    assert result["store"] is True
    assert "streams" in result
    assert "queue_size" in result
    assert "alive" in result
    group.close()


def test_to_dict_returns_dict():
    group = LogGroup(
        id="test123",
        name="TestGroup",
        async_=False,
    )
    result = group.to_dict()
    assert isinstance(result, dict)
    assert result["id"] == "test123"
    assert result["name"] == "testgroup"
    assert result["store"] is True
    assert "streams" in result
    assert isinstance(result["streams"], dict)
    group.close()


def test_to_dict_includes_event_data():
    group = LogGroup(async_=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    result = group.to_dict()
    assert "stream1" in result["streams"]
    assert len(result["streams"]["stream1"]) == 1
    assert result["streams"]["stream1"][0]["message"] == "Test message"
    group.close()


def test_sync_alive_returns_none():
    group = LogGroup(async_=False)
    assert group.alive() is None
    group.close()


def test_async_alive_returns_true():
    group = LogGroup(async_=True)
    assert group.alive() is True
    group.close(timeout=1.0)


def test_async_alive_returns_false_after_close():
    group = LogGroup(async_=True)
    group.close(timeout=1.0)
    assert group.alive() is False


def test_sync_flush_is_noop():
    group = LogGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    assert len(group._events["stream1"]) == 1
    group.close()


def test_async_flush_waits_for_queue():
    group = LogGroup(async_=True)
    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    group.flush()
    assert len(group._events["stream1"]) == 10
    assert group._queue.qsize() == 0
    group.close(timeout=1.0)


def test_sync_close():
    group = LogGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.close()
    assert len(group._events["stream1"]) == 1


def test_async_close_stops_worker():
    group = LogGroup(async_=True)
    assert group._worker.is_alive()
    group.close(timeout=1.0)
    assert not group._worker.is_alive()


def test_async_close_flushes_queue():
    group = LogGroup(async_=True)
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    group.close(timeout=1.0)
    assert len(group._events["stream1"]) == 5


def test_multiple_streams_independent():
    group = LogGroup(async_=False)
    event1 = Log(
        message="Stream1 Event",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Stream2 Event",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream2", event2)
    assert len(group._events["stream1"]) == 1
    assert len(group._events["stream2"]) == 1
    assert group._events["stream1"][0].message == "Stream1 Event"
    assert group._events["stream2"][0].message == "Stream2 Event"
    group.close()


def test_event_ordering_preserved():
    group = LogGroup(async_=False)
    events = []
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        events.append(event)
        group.receive("stream1", event)
    stored = list(group._events["stream1"])
    for i, event in enumerate(events):
        assert stored[i].message == f"Event {i}"
    group.close()


def test_inherits_from_base_group():
    group = LogGroup(async_=False)
    assert hasattr(group, "id")
    assert hasattr(group, "name")
    assert hasattr(group, "receive")
    assert hasattr(group, "flush")
    assert hasattr(group, "close")
    assert hasattr(group, "list_streams")
    assert hasattr(group, "list_events")
    group.close()


def test_defaultdict_creates_new_streams():
    group = LogGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    assert "new_stream" not in group._events
    group.receive("new_stream", event)
    assert "new_stream" in group._events
    group.close()


def test_deque_maxlen_behavior():
    group = LogGroup(async_=False, max_len=3)
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    stored = list(group._events["stream1"])
    assert len(stored) == 3
    assert stored[0].message == "Event 2"
    assert stored[1].message == "Event 3"
    assert stored[2].message == "Event 4"
    group.close()


def test_full_lifecycle_sync():
    group = LogGroup(
        id="lifecycle1",
        name="LifecycleTest",
        async_=False,
    )
    for i in range(3):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    assert len(group._events["stream1"]) == 3
    streams = group.list_streams()
    assert "stream1" in streams
    events = group.list_events("stream1")
    assert len(events) == 3
    group.close()


def test_full_lifecycle_async():
    group = LogGroup(
        id="lifecycle2",
        name="AsyncLifecycleTest",
        async_=True,
    )
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="DEBUG",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    group.flush()
    assert len(group._events["stream1"]) == 5
    streams = group.list_streams()
    assert "stream1" in streams
    events = group.list_events("stream1")
    assert len(events) == 5
    group.close(timeout=1.0)
    assert group.alive() is False


def test_mixed_event_levels():
    group = LogGroup(async_=False)
    event1 = Log(
        message="Debug msg",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Info msg",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event3 = Log(
        message="Warning msg",
        level="WARNING",
        time=datetime.now(pytz.UTC),
    )
    event4 = Log(
        message="Error msg",
        level="ERROR",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream1", event2)
    group.receive("stream1", event3)
    group.receive("stream1", event4)
    assert len(group._events["stream1"]) == 4
    group.close()


def test_empty_stream_name():
    group = LogGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("", event)
    assert "" in group._events
    assert len(group._events[""]) == 1
    group.close()


def test_special_characters_in_stream_name():
    group = LogGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    stream_name = "stream-1_test.name"
    group.receive(stream_name, event)
    assert stream_name in group._events
    assert len(group._events[stream_name]) == 1
    group.close()


def test_async_worker_thread_name():
    group = LogGroup(async_=True, name="WorkerTest")
    assert group._worker.name == "xlog-group:workertest"
    group.close(timeout=1.0)


def test_async_worker_daemon_flag():
    group = LogGroup(async_=True)
    assert group._worker.daemon is True
    group.close(timeout=1.0)


def test_async_queue_maxsize():
    group = LogGroup(async_=True, max_queue=100)
    assert group._queue.maxsize == 100
    group.close(timeout=1.0)


def test_sync_no_queue():
    group = LogGroup(async_=False)
    assert group._queue is None
    assert group._worker is None
    group.close()


def test_describe_async_includes_queue_info():
    group = LogGroup(async_=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    result = group.describe()
    assert "queue_size" in result
    assert "max_queue" in result
    assert result["max_queue"] == 1000
    group.close(timeout=1.0)


def test_describe_sync_queue_info():
    group = LogGroup(async_=False)
    result = group.describe()
    assert result["queue_size"] == 0
    assert result["max_queue"] == 0
    group.close()


def test_name_normalization():
    group = LogGroup(name="MyTestGroup")
    assert group.name == "mytestgroup"
    group.close()


def test_id_auto_generation():
    group1 = LogGroup()
    group2 = LogGroup()
    assert len(group1.id) == 10
    assert len(group2.id) == 10
    assert group1.id != group2.id
    group1.close()
    group2.close()
