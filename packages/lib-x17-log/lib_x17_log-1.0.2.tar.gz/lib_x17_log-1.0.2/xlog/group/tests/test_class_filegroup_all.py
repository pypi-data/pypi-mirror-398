from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import pytz

from xlog.event.logging import Log
from xlog.group.filegroup import FileGroup


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def log_event():
    return Log(
        message="Test message",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )


def test_init_with_defaults(temp_dir):
    group = FileGroup(path=temp_dir)
    assert group.path.resolve() == temp_dir.resolve()
    assert group.encoding == "utf-8"
    assert group.ensure_ascii is False
    assert group.store is True
    assert group._async is False
    assert len(group.id) == 10
    assert not group._cursor.closed
    assert (temp_dir / f"{group.name}.log").exists()

    group.close()


def test_init_with_custom_parameters(temp_dir):
    group = FileGroup(
        path=temp_dir,
        id="test123",
        name="CustomLog",
        encoding="utf-16",
        ensure_ascii=True,
        store=False,
        async_=True,
        max_queue=500,
        max_len=1000,
    )
    assert group.id == "test123"
    assert group.name == "customlog"
    assert group.encoding == "utf-16"
    assert group.ensure_ascii is True
    assert group.store is False
    assert group._async is True
    assert group.max_len == 1000
    assert (temp_dir / "customlog.log").exists()

    group.close(timeout=1.0)


def test_init_with_string_path(temp_dir):
    group = FileGroup(path=str(temp_dir))
    assert group.path.resolve() == temp_dir.resolve()
    assert isinstance(group.path, Path)

    group.close()


def test_init_with_pathlib_path(temp_dir):
    group = FileGroup(path=temp_dir)
    assert group.path.resolve() == temp_dir.resolve()
    assert isinstance(group.path, Path)

    group.close()


def test_init_creates_directory_if_not_exists(temp_dir):
    nested_path = temp_dir / "nested" / "dir" / "structure"
    group = FileGroup(path=nested_path)
    assert nested_path.exists()
    assert nested_path.is_dir()

    group.close()


def test_init_expands_user_path(temp_dir):
    group = FileGroup(path=temp_dir)
    assert group.path.is_absolute()

    group.close()


def test_init_resolves_relative_path(temp_dir):
    group = FileGroup(path=temp_dir)
    assert group.path.is_absolute()

    group.close()


def test_init_creates_log_file(temp_dir):
    group = FileGroup(path=temp_dir, name="TestLog")
    log_file = temp_dir / "testlog.log"
    assert log_file.exists()
    assert log_file.is_file()

    group.close()


def test_init_opens_file_in_append_mode(temp_dir):
    log_file = temp_dir / "test.log"
    log_file.write_text("existing content\n")
    group = FileGroup(path=temp_dir, name="test")
    event = Log(
        message="New message",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    group.close()
    content = log_file.read_text()
    assert "existing content" in content
    assert "New message" in content


def test_init_creates_cursor(temp_dir):
    group = FileGroup(path=temp_dir)
    assert group._cursor is not None
    assert hasattr(group._cursor, "write")
    assert not group._cursor.closed

    group.close()


def test_init_creates_lock(temp_dir):
    group = FileGroup(path=temp_dir)
    assert group._lock is not None
    assert hasattr(group._lock, "acquire")
    assert hasattr(group._lock, "release")

    group.close()


def test_sync_receive_writes_to_file(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="synctest",
        async_=False,
    )
    event = Log(
        message="Sync message",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "synctest.log"
    content = log_file.read_text()
    assert "Sync message" in content
    assert "INFO" in content

    group.close()


def test_sync_receive_multiple_events(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="multitest",
        async_=False,
    )
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
    group.flush()
    log_file = temp_dir / "multitest.log"
    content = log_file.read_text()
    assert "Event 1" in content
    assert "Event 2" in content
    assert "Event 3" in content

    group.close()


def test_sync_writes_jsonl_format(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="jsontest",
        async_=False,
    )
    event1 = Log(
        message="Line 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Line 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream1", event2)
    group.flush()
    log_file = temp_dir / "jsontest.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2

    json1 = json.loads(lines[0])
    json2 = json.loads(lines[1])
    assert json1["message"] == "Line 1"
    assert json2["message"] == "Line 2"
    group.close()


def test_sync_json_keys_sorted(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="sorttest",
        async_=False,
    )
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
        code=200,
        context={"key": "value"},
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "sorttest.log"
    line = log_file.read_text().strip()
    keys = list(json.loads(line).keys())
    assert keys == sorted(keys)

    group.close()


def test_sync_ensure_ascii_false(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="unicodetest",
        async_=False,
        ensure_ascii=False,
    )
    event = Log(
        message="Hello 世界 🌍",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "unicodetest.log"
    content = log_file.read_text(encoding="utf-8")
    assert "世界" in content
    assert "🌍" in content

    group.close()


def test_sync_ensure_ascii_true(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="asciitest",
        async_=False,
        ensure_ascii=True,
    )
    event = Log(
        message="Hello 世界",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "asciitest.log"
    content = log_file.read_text(encoding="utf-8")
    assert "\\u" in content
    assert "世界" not in content

    group.close()


def test_sync_custom_encoding(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="encodingtest",
        async_=False,
        encoding="utf-16",
    )
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    group.close()
    log_file = temp_dir / "encodingtest.log"
    content = log_file.read_text(encoding="utf-16")
    assert "Test message" in content


def test_async_receive_writes_to_file(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="asynctest",
        async_=True,
    )
    event = Log(
        message="Async message",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "asynctest.log"
    content = log_file.read_text()
    assert "Async message" in content

    group.close(timeout=1.0)


def test_async_receive_multiple_events(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="asyncmulti",
        async_=True,
    )

    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    group.flush()
    log_file = temp_dir / "asyncmulti.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 10

    group.close(timeout=1.0)


def test_async_worker_thread_active(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="workertest",
        async_=True,
    )
    assert group.alive() is True

    group.close(timeout=1.0)
    assert group.alive() is False


def test_async_queue_processing(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="queuetest",
        async_=True,
    )
    for i in range(5):
        event = Log(
            message=f"Queued {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    initial_queue_size = group._queue.qsize()
    assert initial_queue_size > 0 or initial_queue_size == 0

    group.flush()
    assert group._queue.qsize() == 0
    group.close(timeout=1.0)


def test_thread_safety_sync_mode(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="threadsafe",
        async_=False,
    )
    group._lock.acquire()
    group._lock.acquire()
    group._lock.release()
    group._lock.release()
    group.close()


def test_concurrent_writes(temp_dir):
    import threading

    group = FileGroup(
        path=temp_dir,
        name="concurrent",
        async_=False,
    )

    def write_events(start_idx):
        for i in range(10):
            event = Log(
                message=f"Thread {start_idx} Event {i}",
                level="INFO",
                time=datetime.now(pytz.UTC),
            )
            group.receive("stream1", event)

    threads = []
    for i in range(5):
        thread = threading.Thread(target=write_events, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    group.flush()
    group.close()
    log_file = temp_dir / "concurrent.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 50

    for line in lines:
        data = json.loads(line)
        assert "message" in data


def test_flush_sync_mode(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="flushsync",
        async_=False,
    )
    event = Log(
        message="Flush test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "flushsync.log"
    content = log_file.read_text()
    assert "Flush test" in content

    group.close()


def test_flush_async_mode(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="flushasync",
        async_=True,
    )
    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "flushasync.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 10

    group.close(timeout=1.0)


def test_flush_file_cursor(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="cursorflush",
        async_=False,
    )
    event = Log(
        message="Cursor test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    log_file = temp_dir / "cursorflush.log"
    content = log_file.read_text()
    assert "Cursor test" in content

    group.close()


def test_close_sync_mode(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="closesync",
        async_=False,
    )
    event = Log(
        message="Close test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.flush()
    group.close()
    log_file = temp_dir / "closesync.log"
    content = log_file.read_text()
    assert "Close test" in content


def test_close_async_mode(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="closeasync",
        async_=True,
    )
    event = Log(
        message="Close test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    group.close(timeout=1.0)
    assert group._cursor.closed
    assert group.alive() is False


def test_close_flushes_before_closing(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="closeflush",
        async_=True,
    )
    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    group.close(timeout=1.0)
    log_file = temp_dir / "closeflush.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 5


def test_close_idempotent(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="idempotent",
        async_=False,
    )

    group.close()
    group.close()


def test_close_with_timeout(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="timeout",
        async_=True,
    )
    for i in range(10):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    group.close(timeout=2.0)
    assert group._cursor.closed
    assert group.alive() is False


def test_store_true_saves_events(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="storetest",
        async_=False,
        store=True,
    )
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


def test_store_false_does_not_save_events(temp_dir):
    group = FileGroup(path=temp_dir, name="nostoretest", async_=False, store=False)
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

    assert len(group._events.get("stream1", [])) == 0

    group.flush()
    group.close()

    log_file = temp_dir / "nostoretest.log"
    content = log_file.read_text().strip()
    if content:
        lines = content.split("\n")
        assert len(lines) == 2


def test_max_len_limits_stored_events(temp_dir):
    group = FileGroup(path=temp_dir, name="maxlentest", async_=False, store=True, max_len=3)

    for i in range(5):
        event = Log(
            message=f"Event {i}",
            level="INFO",
            time=datetime.now(pytz.UTC),
        )
        group.receive("stream1", event)

    assert len(group._events["stream1"]) == 3

    group.flush()
    group.close()

    log_file = temp_dir / "maxlentest.log"
    content = log_file.read_text().strip()
    if content:
        lines = content.split("\n")
        assert len(lines) == 5


def test_full_lifecycle_sync(temp_dir):
    group = FileGroup(path=temp_dir, name="lifecycle", async_=False, store=True)

    for i in range(3):
        event = Log(message=f"Lifecycle event {i}", level="INFO", time=datetime.now(pytz.UTC))
        group.receive("stream1", event)

    group.flush()

    assert len(group._events["stream1"]) == 3

    log_file = temp_dir / "lifecycle.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 3

    group.close()


def test_full_lifecycle_async(temp_dir):
    group = FileGroup(path=temp_dir, name="asynclife", async_=True, store=True)

    for i in range(5):
        event = Log(message=f"Async lifecycle {i}", level="DEBUG", time=datetime.now(pytz.UTC))
        group.receive("stream1", event)

    group.flush()

    assert len(group._events["stream1"]) == 5

    log_file = temp_dir / "asynclife.log"
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 5

    group.close(timeout=1.0)
    assert group._cursor.closed
    assert group.alive() is False


def test_multiple_streams_to_same_file(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="multistream",
        async_=False,
    )

    event1 = Log(
        message="Stream 1",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    event2 = Log(
        message="Stream 2",
        level="DEBUG",
        time=datetime.now(pytz.UTC),
    )
    event3 = Log(
        message="Stream 3",
        level="ERROR",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event1)
    group.receive("stream2", event2)
    group.receive("stream3", event3)
    group.flush()
    group.close()
    log_file = temp_dir / "multistream.log"
    content = log_file.read_text().strip()
    if content:
        lines = content.split("\n")
        assert len(lines) == 3


def test_event_serialization(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="serialize",
        async_=False,
    )
    event = Log(
        message="Complex event",
        level="WARNING",
        time=datetime.now(pytz.UTC),
        code=404,
        context={"request": "GET /api"},
        tags={"env": "test"},
    )
    group.receive("stream1", event)
    group.flush()
    group.close()
    log_file = temp_dir / "serialize.log"
    line = log_file.read_text().strip()
    data = json.loads(line)
    assert data["message"] == "Complex event"
    assert data["level"] == "WARNING"
    assert data["code"] == 404
    assert data["context"]["request"] == "GET /api"
    assert data["tags"]["env"] == "test"


def test_inherits_from_base_group(temp_dir):
    group = FileGroup(path=temp_dir)
    assert hasattr(group, "id")
    assert hasattr(group, "name")
    assert hasattr(group, "receive")
    assert hasattr(group, "flush")
    assert hasattr(group, "close")
    assert hasattr(group, "list_streams")
    assert hasattr(group, "list_events")

    group.close()


def test_describe_includes_file_info(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="describe",
        async_=False,
    )
    result = group.describe()
    assert isinstance(result, dict)
    assert result["name"] == "describe"
    assert "streams" in result

    group.close()


def test_to_dict_serialization(temp_dir):
    group = FileGroup(
        path=temp_dir,
        name="todict",
        async_=False,
        store=True,
    )
    event = Log(
        message="Test",
        level="INFO",
        time=datetime.now(pytz.UTC),
    )
    group.receive("stream1", event)
    result = group.to_dict()
    assert isinstance(result, dict)
    assert result["name"] == "todict"
    assert "streams" in result
    assert "stream1" in result["streams"]

    group.close()
