import time
from datetime import datetime

import pytz

from xlog.event.logging import Log
from xlog.group.base import BaseGroup


class MockGroup(BaseGroup):
    def __init__(self, *args, **kwargs):
        self.consumed_events = []
        self.dropped_events = []
        self.error_events = []
        self.closed = False
        super().__init__(*args, **kwargs)

    def _consume(self, stream: str, event):
        self.consumed_events.append((stream, event))

    def _on_drop(self, stream: str, event):
        self.dropped_events.append((stream, event))

    def _on_close(self):
        self.closed = True

    def _on_error(self, stream: str, event, error: Exception):
        self.error_events.append((stream, event, error))


# ---------- ASYNC MODE TESTS ----------


def test_async_init_with_defaults():
    group = MockGroup(async_=True)
    assert group.store is True
    assert group.max_len == 100_000
    assert group._queue.maxsize == 1000
    assert group._worker.is_alive()
    assert group._worker.daemon is True
    assert group._async is True
    assert len(group.id) == 10

    group.close(timeout=1.0)
    assert not group._worker.is_alive()


def test_async_init_with_custom_parameters():
    group = MockGroup(
        async_=True,
        id="test123",
        name="TestGroup",
        store=False,
        max_queue=500,
        max_len=1000,
    )
    assert group.id == "test123"
    assert group.name == "testgroup"
    assert group.store is False
    assert group.max_len == 1000
    assert group._queue.maxsize == 500
    assert group._async is True

    group.close(timeout=1.0)


def test_async_init_with_none_max_len():
    group = MockGroup(async_=True, max_len=None)
    assert group.max_len is None

    group.close(timeout=1.0)


def test_async_worker_thread_starts_automatically():
    group = MockGroup(async_=True)
    assert group._worker.is_alive()
    assert group._worker.name == f"xlog-group:{group.name}"

    group.close(timeout=1.0)


def test_async_alive_returns_true():
    group = MockGroup(async_=True)
    assert group.alive() is True

    group.close(timeout=1.0)


def test_async_alive_returns_false_after_close():
    group = MockGroup(async_=True)
    group.close(timeout=1.0)
    assert group.alive() is False


def test_async_receive_adds_event_to_queue():
    group = MockGroup(async_=True)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    time.sleep(0.2)

    assert len(group.consumed_events) == 1
    assert group.consumed_events[0] == ("stream1", event)
    group.close(timeout=1.0)


def test_async_receive_multiple_events():
    group = MockGroup(async_=True)
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

    group.flush()  # Wait for all events to be processed

    assert len(group.consumed_events) == 3
    assert ("stream1", event1) in group.consumed_events
    assert ("stream2", event2) in group.consumed_events
    assert ("stream1", event3) in group.consumed_events

    group.close(timeout=1.0)


def test_async_receive_drops_oldest_when_queue_full():
    class SlowMockGroup(MockGroup):
        def _consume(self, stream, event):
            time.sleep(0.1)
            super()._consume(stream, event)

    group = SlowMockGroup(async_=True, max_queue=3)

    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    time.sleep(0.5)
    assert len(group.dropped_events) > 0

    group.close(timeout=5.0)


def test_async_receive_after_stop_drops_event():
    group = MockGroup(async_=True)
    group._stop.set()

    event = Log(
        message="Late event",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    time.sleep(0.1)
    assert len(group.dropped_events) > 0

    group.close(timeout=1.0)


def test_async_store_true_saves_events():
    group = MockGroup(async_=True, store=True)
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

    group.flush()

    assert "stream1" in group._events
    assert len(group._events["stream1"]) == 2

    group.close(timeout=1.0)


def test_async_store_false_does_not_save_events():
    group = MockGroup(async_=True, store=False)
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
    group.flush()
    assert len(group.consumed_events) == 2
    assert len(group._events.get("stream1", [])) == 0

    group.close(timeout=1.0)


def test_async_store_respects_max_len():
    group = MockGroup(async_=True, store=True, max_len=3)

    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    group.flush()
    assert len(group._events["stream1"]) == 3

    group.close(timeout=1.0)


def test_async_flush_waits_for_queue_processing():
    group = MockGroup(async_=True)

    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    group.flush()
    assert len(group.consumed_events) == 10
    assert group._queue.qsize() == 0

    group.close(timeout=1.0)


def test_async_close_stops_worker_thread():
    group = MockGroup(async_=True)
    assert group._worker.is_alive()

    group.close(timeout=1.0)
    assert not group._worker.is_alive()
    assert group.closed is True


def test_async_close_flushes_queue_first():
    group = MockGroup(async_=True)
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    group.close(timeout=1.0)
    assert len(group.consumed_events) == 5


def test_async_on_error_hook_called():
    class ErrorGroup(MockGroup):
        def _consume(self, stream, event):
            super()._consume(stream, event)
            if "error" in event.message:
                raise ValueError("Test error")

    group = ErrorGroup(async_=True)
    event_ok = Log(
        message="OK event",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event_error = Log(
        message="error event",
        level="ERROR",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event_ok)
    group.receive("stream1", event_error)
    group.flush()
    assert len(group.error_events) > 0

    group.close(timeout=1.0)


# ---------- SYNC MODE TESTS ----------


def test_sync_init_with_defaults():
    group = MockGroup(async_=False)
    assert group.store is True
    assert group.max_len is None
    assert group._queue is None
    assert group._worker is None
    assert group._async is False
    assert len(group.id) == 10

    group.close()


def test_sync_init_with_custom_parameters():
    group = MockGroup(
        async_=False,
        id="test456",
        name="SyncGroup",
        store=False,
    )
    assert group.id == "test456"
    assert group.name == "syncgroup"
    assert group.store is False
    assert group._async is False
    assert group._queue is None
    assert group._worker is None

    group.close()


def test_sync_alive_returns_none():
    group = MockGroup(async_=False)
    assert group.alive() is None

    group.close()


def test_sync_receive_processes_immediately():
    group = MockGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    assert len(group.consumed_events) == 1
    assert group.consumed_events[0] == ("stream1", event)

    group.close()


def test_sync_receive_multiple_events():
    group = MockGroup(async_=False)
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
    assert len(group.consumed_events) == 3
    assert ("stream1", event1) in group.consumed_events
    assert ("stream2", event2) in group.consumed_events
    assert ("stream1", event3) in group.consumed_events

    group.close()


def test_sync_store_true_saves_events():
    group = MockGroup(async_=False, store=True)
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


def test_sync_store_false_does_not_save_events():
    group = MockGroup(async_=False, store=False)
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
    assert len(group.consumed_events) == 2
    assert len(group._events.get("stream1", [])) == 0

    group.close()


def test_sync_flush_is_noop():
    group = MockGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    assert len(group.consumed_events) == 1

    group.close()


def test_sync_close_is_noop():
    group = MockGroup(async_=False)
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.close(timeout=1.0)
    assert len(group.consumed_events) == 1

    group.close()


def test_sync_no_dropping_behavior():
    group = MockGroup(async_=False)
    for i in range(100):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    assert len(group.consumed_events) == 100
    assert len(group.dropped_events) == 0

    group.close()


def test_sync_store_with_max_len():
    group = MockGroup(async_=False, store=True, max_len=3)
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    assert len(group._events["stream1"]) == 3
    group.close()


# ---------- COMMON TESTS (work for both async and sync) ----------


def test_list_streams_empty():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode)
        assert group.list_streams() == []
        group.close(timeout=1.0)


def test_list_streams_with_events():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
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
        if async_mode:
            group.flush()

        streams = group.list_streams()
        assert len(streams) == 3
        assert "stream1" in streams
        assert "stream2" in streams
        assert "stream3" in streams
        group.close(timeout=1.0)


def test_list_events_empty():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode)
        assert group.list_events() == []
        group.close(timeout=1.0)


def test_list_events_with_stored_events():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
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
        if async_mode:
            group.flush()

        events = group.list_events()
        assert len(events) == 3
        assert event1 in events
        assert event2 in events
        assert event3 in events
        group.close(timeout=1.0)


def test_list_events_by_stream():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
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

        if async_mode:
            group.flush()

        stream1_events = group.list_events("stream1")
        assert len(stream1_events) == 1
        assert event1 in stream1_events

        stream2_events = group.list_events("stream2")
        assert len(stream2_events) == 1
        assert event2 in stream2_events

        group.close(timeout=1.0)


def test_describe_returns_dict():
    for async_mode in [True, False]:
        group = MockGroup(
            async_=async_mode,
            id="test123",
            name="TestGroup",
            store=True,
        )
        result = group.describe()
        assert isinstance(result, dict)
        assert result["id"] == "test123"
        assert result["name"] == "testgroup"
        assert result["store"] is True
        assert "streams" in result
        assert "queue_size" in result
        assert "alive" in result
        if async_mode:
            assert result["alive"] is True
            assert result["max_queue"] > 0
        else:
            assert result["alive"] is None
            assert result["max_queue"] == 0

        group.close(timeout=1.0)


def test_to_dict_returns_dict():
    for async_mode in [True, False]:
        group = MockGroup(
            async_=async_mode,
            id="test123",
            name="TestGroup",
            store=True,
        )
        result = group.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == "test123"
        assert result["name"] == "testgroup"
        assert result["store"] is True
        assert "streams" in result
        assert isinstance(result["streams"], dict)

        group.close(timeout=1.0)


def test_to_dict_includes_event_data():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
        event = Log(
            message="Test message",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

        if async_mode:
            group.flush()

        result = group.to_dict()
        assert "stream1" in result["streams"]
        assert len(result["streams"]["stream1"]) == 1
        assert result["streams"]["stream1"][0]["message"] == "Test message"

        group.close(timeout=1.0)


def test_multiple_streams_independent():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
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
        if async_mode:
            group.flush()
        assert len(group._events["stream1"]) == 1
        assert len(group._events["stream2"]) == 1
        assert group._events["stream1"][0].message == "Stream1 Event"
        assert group._events["stream2"][0].message == "Stream2 Event"

        group.close(timeout=1.0)


def test_event_ordering_preserved():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
        events = []
        for i in range(5):
            event = Log(
                message=f"Event {i}",
                level="INFO",
                time=datetime.now(pytz.UTC),
            )
            events.append(event)
            group.receive("stream1", event)

        if async_mode:
            group.flush()

        stored = list(group._events["stream1"])
        for i, event in enumerate(events):
            assert stored[i].message == f"Event {i}"

        group.close(timeout=1.0)


def test_inherits_from_log_component():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode)
        assert hasattr(group, "id")
        assert hasattr(group, "name")
        group.close(timeout=1.0)


def test_store_converts_to_bool():
    for async_mode in [True, False]:
        group1 = MockGroup(async_=async_mode, store=1)
        assert group1.store is True

        group1.close(timeout=1.0)
        group2 = MockGroup(async_=async_mode, store=0)
        assert group2.store is False

        group2.close(timeout=1.0)
        group3 = MockGroup(async_=async_mode, store="yes")
        assert group3.store is True
        group3.close(timeout=1.0)


def test_async_converts_to_bool():
    group1 = MockGroup(async_=1)
    assert group1._async is True

    group1.close(timeout=1.0)
    group2 = MockGroup(async_=0)
    assert group2._async is False

    group2.close(timeout=1.0)
    group3 = MockGroup(async_="yes")
    assert group3._async is True

    group3.close(timeout=1.0)


def test_defaultdict_creates_new_streams():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True)
        event = Log(
            message="Test",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        assert "new_stream" not in group._events

        group.receive("new_stream", event)
        if async_mode:
            group.flush()
        assert "new_stream" in group._events

        group.close(timeout=1.0)


def test_deque_maxlen_behavior():
    for async_mode in [True, False]:
        group = MockGroup(async_=async_mode, store=True, max_len=3)

        for i in range(5):
            event = Log(
                message=f"Event {i}",
                level="INFO",
                time=datetime.now(pytz.UTC),
            )
            group.receive("stream1", event)

        if async_mode:
            group.flush()

        stored = list(group._events["stream1"])
        assert len(stored) == 3
        assert stored[0].message == "Event 2"
        assert stored[1].message == "Event 3"
        assert stored[2].message == "Event 4"

        group.close(timeout=1.0)


def test_consume_must_be_implemented():
    assert hasattr(BaseGroup, "_consume")
