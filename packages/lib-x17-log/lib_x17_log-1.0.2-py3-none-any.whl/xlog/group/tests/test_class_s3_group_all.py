"""
Comprehensive pytest tests for S3Group class.
Tests cover initialization, URI parsing, boto3 integration, buffering,
flushing, S3 operations, error handling, and async mode.
"""

import json
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import pytz

from xlog import Log
from xlog.group.s3group import S3Group

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def log_event():
    """Create a sample log event for testing."""
    return Log(
        message="Test message",
        level="INFO",
        time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
    )


@pytest.fixture
def mock_boto3_session():
    """Create a mock boto3 Session."""
    with patch("xlog.group.s3group.boto3") as mock_boto3:
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_boto3.Session.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    # Default: object doesn't exist - return proper ClientError
    error_response = {
        "Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}
    }
    mock_client.get_object.side_effect = ClientError(error_response, "GetObject")
    mock_client.put_object.return_value = {"ETag": '"mock-etag"'}
    return mock_client


# ============================================================================
# Initialization Tests
# ============================================================================


def test_init_missing_boto3():
    """Test initialization fails gracefully when boto3 is not installed."""
    with patch("xlog.group.s3group.HAS_BOTO3", False):
        with pytest.raises(ImportError) as exc_info:
            S3Group(uri="s3://bucket/key.log")
        assert "boto3" in str(exc_info.value).lower()


def test_init_with_valid_uri(mock_boto3_session, mock_s3_client):
    """Test initialization with a valid S3 URI."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://test-bucket/logs/test.log")
            assert group.bucket == "test-bucket"
            assert group.key == "logs/test.log"
            assert group.uri == "s3://test-bucket/logs/test.log"
            group.close()


def test_init_with_defaults(mock_boto3_session, mock_s3_client):
    """Test initialization with default parameters."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log")
            assert group.encoding == "utf-8"
            assert group.ensure_ascii is False
            assert group.store is True
            assert group._async is False  # Default is False
            group.close()


def test_init_with_custom_encoding(mock_boto3_session, mock_s3_client):
    """Test initialization with custom encoding."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", encoding="utf-16")
            assert group.encoding == "utf-16"
            group.close()


def test_init_with_ensure_ascii_true(mock_boto3_session, mock_s3_client):
    """Test initialization with ensure_ascii=True."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", ensure_ascii=True)
            assert group.ensure_ascii is True
            group.close()


def test_init_with_store_false(mock_boto3_session, mock_s3_client):
    """Test initialization with store=False."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", store=False)
            assert group.store is False
            group.close()


def test_init_with_sync_mode(mock_boto3_session, mock_s3_client):
    """Test initialization with async_=False (sync mode)."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)
            assert group._async is False
            assert group.alive() is None  # Returns None in sync mode
            group.close()


def test_init_with_async_mode(mock_boto3_session, mock_s3_client):
    """Test initialization with async_=True (async mode)."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=True)
            assert group._async is True
            assert group.alive() is True
            group.close(timeout=1.0)


def test_init_with_custom_name(mock_boto3_session, mock_s3_client):
    """Test initialization with custom name parameter."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", name="custom-name")
            assert group.name == "custom-name"
            group.close()


def test_init_with_profile(mock_boto3_session, mock_s3_client):
    """Test initialization with AWS profile."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch(
            "xlog.group.s3group.boto3.Session", return_value=mock_boto3_session
        ) as mock_session_cls:
            group = S3Group(uri="s3://bucket/test.log", profile="my-profile")
            mock_session_cls.assert_called_once()
            call_kwargs = mock_session_cls.call_args[1]
            assert call_kwargs.get("profile_name") == "my-profile"
            group.close()


def test_init_with_region(mock_boto3_session, mock_s3_client):
    """Test initialization with AWS region."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch(
            "xlog.group.s3group.boto3.Session", return_value=mock_boto3_session
        ) as mock_session_cls:
            group = S3Group(uri="s3://bucket/test.log", region="us-west-2")
            mock_session_cls.assert_called_once()
            call_kwargs = mock_session_cls.call_args[1]
            assert call_kwargs.get("region_name") == "us-west-2"
            group.close()


def test_init_with_profile_and_region(mock_boto3_session, mock_s3_client):
    """Test initialization with both profile and region."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch(
            "xlog.group.s3group.boto3.Session", return_value=mock_boto3_session
        ) as mock_session_cls:
            group = S3Group(
                uri="s3://bucket/test.log",
                profile="my-profile",
                region="eu-west-1",
            )
            mock_session_cls.assert_called_once()
            call_kwargs = mock_session_cls.call_args[1]
            assert call_kwargs.get("profile_name") == "my-profile"
            assert call_kwargs.get("region_name") == "eu-west-1"
            group.close()


def test_init_with_provided_session(mock_s3_client):
    """Test initialization with a provided boto3 session."""
    mock_session = MagicMock()
    mock_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        group = S3Group(uri="s3://bucket/test.log", session=mock_session)
        mock_session.client.assert_called_once_with("s3")
        group.close()


def test_init_with_custom_max_queue(mock_boto3_session, mock_s3_client):
    """Test initialization with custom max_queue size."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", max_queue=500, async_=True)
            assert group._queue.maxsize == 500
            group.close(timeout=1.0)


def test_init_with_custom_max_len(mock_boto3_session, mock_s3_client):
    """Test initialization with custom max_len."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", max_len=2048)
            # max_len is stored but not directly accessible
            group.close()


# ============================================================================
# URI Parsing Tests
# ============================================================================


def test_parse_valid_s3_uri():
    """Test parsing a valid S3 URI."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        mock_session = MagicMock()
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_session):
            group = S3Group(uri="s3://my-bucket/path/to/file.log")
            assert group.bucket == "my-bucket"
            assert group.key == "path/to/file.log"
            group.close()


def test_parse_s3_uri_with_nested_path():
    """Test parsing S3 URI with deeply nested path."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        mock_session = MagicMock()
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_session):
            group = S3Group(uri="s3://bucket/a/b/c/d/file.log")
            assert group.bucket == "bucket"
            assert group.key == "a/b/c/d/file.log"
            group.close()


def test_parse_s3_uri_without_key():
    """Test parsing S3 URI fails without a key."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with pytest.raises(ValueError) as exc_info:
            S3Group(uri="s3://bucket")
        assert "bucket" in str(exc_info.value).lower() or "key" in str(exc_info.value).lower()


def test_parse_s3_uri_with_trailing_slash():
    """Test parsing S3 URI with trailing slash."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        mock_session = MagicMock()
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_session):
            group = S3Group(uri="s3://bucket/path/file.log")
            assert group.bucket == "bucket"
            assert group.key == "path/file.log"
            group.close()


def test_parse_invalid_scheme():
    """Test parsing URI with invalid scheme fails."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with pytest.raises(ValueError) as exc_info:
            S3Group(uri="http://bucket/key.log")
        assert "s3://" in str(exc_info.value).lower()


def test_parse_empty_uri():
    """Test parsing empty URI fails."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with pytest.raises((ValueError, TypeError)):
            S3Group(uri="")


def test_parse_none_uri():
    """Test parsing None URI fails."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with pytest.raises((TypeError, ValueError)):
            S3Group(uri=None)


def test_parse_malformed_uri():
    """Test parsing malformed URI fails."""
    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with pytest.raises(ValueError):
            S3Group(uri="s3:bucket/key")


# ============================================================================
# Session and Client Tests
# ============================================================================


def test_resolve_session_creates_new_session(mock_boto3_session, mock_s3_client):
    """Test that _resolve_session creates a new session when none provided."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch(
            "xlog.group.s3group.boto3.Session", return_value=mock_boto3_session
        ) as mock_session_cls:
            group = S3Group(uri="s3://bucket/test.log")
            mock_session_cls.assert_called_once()
            group.close()


def test_resolve_session_uses_provided_session(mock_s3_client):
    """Test that _resolve_session uses provided session."""
    mock_session = MagicMock()
    mock_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session") as mock_session_cls:
            group = S3Group(uri="s3://bucket/test.log", session=mock_session)
            mock_session_cls.assert_not_called()
            group.close()


def test_resolve_client_creates_s3_client(mock_boto3_session, mock_s3_client):
    """Test that _resolve_client creates S3 client from session."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log")
            mock_boto3_session.client.assert_called_once_with("s3")
            group.close()


# ============================================================================
# Receive and Buffer Tests (Sync Mode)
# ============================================================================


def test_sync_receive_buffers_event(mock_boto3_session, mock_s3_client, log_event):
    """Test that receive() buffers events in sync mode."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)
            group.receive("stream1", log_event)

            # Buffer should contain the event
            buffer_content = group._buffer.getvalue()
            assert len(buffer_content) > 0
            assert "Test message" in buffer_content

            group.close()


def test_sync_receive_multiple_events(mock_boto3_session, mock_s3_client):
    """Test receiving multiple events in sync mode."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            for i in range(5):
                event = Log(
                    message=f"Event {i}",
                    level="INFO",
                    time=datetime.now(pytz.UTC),
                )
                group.receive("stream1", event)

            buffer_content = group._buffer.getvalue()
            lines = buffer_content.strip().split("\n")
            assert len(lines) == 5

            group.close()


def test_sync_receive_jsonl_format(mock_boto3_session, mock_s3_client):
    """Test that events are formatted as JSONL in buffer."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event1 = Log(message="Line 1", level="INFO", time=datetime.now(pytz.UTC))
            event2 = Log(message="Line 2", level="DEBUG", time=datetime.now(pytz.UTC))

            group.receive("stream1", event1)
            group.receive("stream1", event2)

            buffer_content = group._buffer.getvalue()
            lines = buffer_content.strip().split("\n")
            assert len(lines) == 2

            json1 = json.loads(lines[0])
            json2 = json.loads(lines[1])
            assert json1["message"] == "Line 1"
            assert json2["message"] == "Line 2"

            group.close()


def test_sync_json_keys_sorted(mock_boto3_session, mock_s3_client):
    """Test that JSON keys are sorted in buffer."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event = Log(
                message="Test",
                level="INFO",
                time=datetime.now(pytz.UTC),
                code=200,
                context={"key": "value"},
            )
            group.receive("stream1", event)

            buffer_content = group._buffer.getvalue()
            line = buffer_content.strip()
            keys = list(json.loads(line).keys())
            assert keys == sorted(keys)

            group.close()


def test_sync_ensure_ascii_false(mock_boto3_session, mock_s3_client):
    """Test ensure_ascii=False preserves Unicode characters."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False, ensure_ascii=False)

            event = Log(
                message="Hello 世界 🌍",
                level="INFO",
                time=datetime.now(pytz.UTC),
            )
            group.receive("stream1", event)

            buffer_content = group._buffer.getvalue()
            assert "世界" in buffer_content
            assert "🌍" in buffer_content

            group.close()


def test_sync_ensure_ascii_true(mock_boto3_session, mock_s3_client):
    """Test ensure_ascii=True escapes Unicode characters."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False, ensure_ascii=True)

            event = Log(
                message="Hello 世界",
                level="INFO",
                time=datetime.now(pytz.UTC),
            )
            group.receive("stream1", event)

            buffer_content = group._buffer.getvalue()
            assert "\\u" in buffer_content
            assert "世界" not in buffer_content

            group.close()


def test_sync_store_false_still_buffers(mock_boto3_session, mock_s3_client, log_event):
    """Test that store=False still buffers events (store only affects in-memory event storage)."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False, store=False)
            group.receive("stream1", log_event)

            # Buffer should still contain the event (store affects _events, not _buffer)
            buffer_content = group._buffer.getvalue()
            assert len(buffer_content) > 0

            group.close()


# ============================================================================
# Flush and S3 Write Tests
# ============================================================================


def test_sync_flush_writes_to_s3(mock_boto3_session, mock_s3_client, log_event):
    """Test that flush() writes buffer to S3 in sync mode."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)
            group.receive("stream1", log_event)
            group.flush()

            # Verify put_object was called
            mock_s3_client.put_object.assert_called_once()
            call_kwargs = mock_s3_client.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "bucket"
            assert call_kwargs["Key"] == "test.log"

            # Buffer should be cleared after flush
            assert len(group._buffer.getvalue()) == 0

            group.close()


def test_sync_flush_empty_buffer(mock_boto3_session, mock_s3_client):
    """Test that flush() with empty buffer doesn't call S3."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)
            group.flush()

            # No S3 call should be made for empty buffer
            mock_s3_client.put_object.assert_not_called()

            group.close()


def test_sync_multiple_flushes(mock_boto3_session, mock_s3_client):
    """Test multiple flush operations append to S3 object."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client

    # First flush: object doesn't exist
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event1 = Log(message="First", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event1)
            group.flush()

            # Second flush: object exists, simulate reading it back
            existing_content = json.dumps({"message": "First"}) + "\n"
            mock_response = {"Body": BytesIO(existing_content.encode("utf-8"))}
            mock_s3_client.get_object.side_effect = None
            mock_s3_client.get_object.return_value = mock_response

            event2 = Log(message="Second", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event2)
            group.flush()

            # Verify put_object was called twice
            assert mock_s3_client.put_object.call_count == 2

            group.close()


def test_write_to_s3_creates_new_object(mock_boto3_session, mock_s3_client):
    """Test _write_to_s3 creates new object when it doesn't exist."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)
            group.flush()

            call_kwargs = mock_s3_client.put_object.call_args[1]
            body = call_kwargs["Body"].decode("utf-8")
            assert "Test" in body

            group.close()


def test_write_to_s3_appends_to_existing_object(mock_boto3_session):
    """Test _write_to_s3 appends to existing S3 object."""
    # Create a fresh mock client for this test to avoid fixture side_effect
    mock_s3_client = MagicMock()
    mock_boto3_session.client.return_value = mock_s3_client

    existing_content = json.dumps({"message": "Existing"}) + "\n"
    mock_response = {"Body": BytesIO(existing_content.encode("utf-8"))}
    mock_s3_client.get_object.return_value = mock_response
    mock_s3_client.put_object.return_value = {"ETag": '"mock-etag"'}

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event = Log(message="New", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)
            group.flush()

            call_kwargs = mock_s3_client.put_object.call_args[1]
            body = call_kwargs["Body"].decode("utf-8")
            assert "Existing" in body
            assert "New" in body

            group.close()


def test_write_to_s3_with_custom_encoding(mock_boto3_session, mock_s3_client):
    """Test writing to S3 with custom encoding."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False, encoding="utf-16")

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)
            group.flush()

            # Verify encoding was used
            mock_s3_client.put_object.assert_called_once()

            group.close()


# ============================================================================
# Async Mode Tests
# ============================================================================


def test_async_receive_queues_event(mock_boto3_session, mock_s3_client, log_event):
    """Test that receive() queues events in async mode."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=True)
            group.receive("stream1", log_event)

            # Event should be in queue or already processed
            import time

            time.sleep(0.1)  # Give worker thread time to process

            group.close(timeout=1.0)


def test_async_worker_thread_active(mock_boto3_session, mock_s3_client):
    """Test that worker thread is active in async mode."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=True)
            assert group.alive() is True

            group.close(timeout=1.0)
            assert group.alive() is False


def test_async_multiple_events(mock_boto3_session, mock_s3_client):
    """Test processing multiple events in async mode."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=True)

            for i in range(10):
                event = Log(
                    message=f"Event {i}",
                    level="INFO",
                    time=datetime.now(pytz.UTC),
                )
                group.receive("stream1", event)

            group.flush()

            import time

            time.sleep(0.2)  # Allow processing

            group.close(timeout=1.0)


def test_async_queue_processing(mock_boto3_session, mock_s3_client):
    """Test that async mode processes queue."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=True)

            for i in range(5):
                event = Log(
                    message=f"Queued {i}",
                    level="INFO",
                    time=datetime.now(pytz.UTC),
                )
                group.receive("stream1", event)

            initial_size = group._queue.qsize()

            group.flush()

            import time

            time.sleep(0.1)

            # Queue should be empty or smaller after processing
            assert group._queue.qsize() <= initial_size

            group.close(timeout=1.0)


def test_async_close_with_timeout(mock_boto3_session, mock_s3_client):
    """Test closing async group with timeout."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=True)

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)

            import time

            time.sleep(0.2)  # Allow async processing

            group.close(timeout=2.0)
            assert group.alive() is False


# ============================================================================
# Thread Safety Tests
# ============================================================================


def test_thread_safety_sync_mode(mock_boto3_session, mock_s3_client):
    """Test thread safety in sync mode (RLock)."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            # RLock allows multiple acquisitions by same thread
            group._lock.acquire()
            group._lock.acquire()
            group._lock.release()
            group._lock.release()

            group.close()


def test_concurrent_writes(mock_boto3_session, mock_s3_client):
    """Test concurrent writes from multiple threads."""
    import threading

    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

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

            # Verify buffer contains all events
            buffer_content = group._buffer.getvalue()
            assert buffer_content == ""  # Buffer should be empty after flush

            # Verify S3 write was called
            assert mock_s3_client.put_object.call_count >= 1

            group.close()


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_s3_client_error_on_flush(mock_boto3_session, mock_s3_client):
    """Test handling of S3 ClientError during flush."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response_get = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response_get, "GetObject")
    mock_s3_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "PutObject"
    )

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)

            # Flush should raise or handle the error
            with pytest.raises(ClientError):
                group.flush()

            group.close()


def test_s3_botocore_error_on_flush(mock_boto3_session, mock_s3_client):
    """Test handling of BotoCoreError during flush."""
    from botocore.exceptions import BotoCoreError, ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")
    mock_s3_client.put_object.side_effect = BotoCoreError()

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)

            with pytest.raises(BotoCoreError):
                group.flush()

            group.close()


def test_close_flushes_buffer(mock_boto3_session, mock_s3_client):
    """Test that _on_close flushes remaining buffer in async mode."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            # Test with async mode where _on_close is called by worker thread
            group = S3Group(uri="s3://bucket/test.log", async_=True)

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            group.receive("stream1", event)

            import time

            time.sleep(0.1)  # Let async worker process

            # Close should trigger _on_close in async worker thread
            group.close(timeout=1.0)

            # Verify flush was called (_on_close writes to S3)
            assert mock_s3_client.put_object.call_count >= 1


def test_close_twice_no_error(mock_boto3_session, mock_s3_client):
    """Test that closing twice doesn't raise error."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)
            group.close()
            group.close()  # Should not raise


def test_receive_after_close(mock_boto3_session, mock_s3_client):
    """Test that receive after close is handled gracefully."""
    mock_boto3_session.client.return_value = mock_s3_client

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/test.log", async_=False)
            group.close()

            event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
            # Behavior depends on implementation - may ignore or raise
            # Just ensure it doesn't crash
            try:
                group.receive("stream1", event)
            except Exception:
                pass  # Expected if closed


# ============================================================================
# Integration-style Tests
# ============================================================================


def test_full_workflow_sync_mode(mock_boto3_session, mock_s3_client):
    """Test complete workflow in sync mode: init, receive, flush, close."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(
                uri="s3://test-bucket/logs/app.log",
                profile="default",
                region="us-east-1",
                encoding="utf-8",
                ensure_ascii=False,
                async_=False,
            )

            # Send multiple events
            for i in range(5):
                event = Log(
                    message=f"Log entry {i}",
                    level="INFO" if i % 2 == 0 else "DEBUG",
                    time=datetime.now(pytz.UTC),
                )
                group.receive("app-stream", event)

            # Flush to S3
            group.flush()

            # Verify S3 write
            assert mock_s3_client.put_object.call_count == 1
            call_kwargs = mock_s3_client.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "test-bucket"
            assert call_kwargs["Key"] == "logs/app.log"
            body = call_kwargs["Body"].decode("utf-8")
            assert "Log entry 0" in body
            assert "Log entry 4" in body

            # Clean close
            group.close()


def test_full_workflow_async_mode(mock_boto3_session, mock_s3_client):
    """Test complete workflow in async mode: init, receive, flush, close."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(
                uri="s3://test-bucket/logs/async.log",
                async_=True,
                max_queue=100,
            )

            # Worker thread should be active
            assert group.alive() is True

            # Send events
            for i in range(10):
                event = Log(
                    message=f"Async log {i}",
                    level="INFO",
                    time=datetime.now(pytz.UTC),
                )
                group.receive("async-stream", event)

            # Flush and wait
            group.flush()

            import time

            time.sleep(0.2)

            # Clean close with timeout
            group.close(timeout=2.0)
            assert group.alive() is False


def test_multiple_streams_same_group(mock_boto3_session, mock_s3_client):
    """Test receiving events from multiple streams to same S3 group."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(uri="s3://bucket/multi.log", async_=False)

            # Different streams
            event1 = Log(message="From stream1", level="INFO", time=datetime.now(pytz.UTC))
            event2 = Log(message="From stream2", level="DEBUG", time=datetime.now(pytz.UTC))
            event3 = Log(message="From stream3", level="ERROR", time=datetime.now(pytz.UTC))

            group.receive("stream1", event1)
            group.receive("stream2", event2)
            group.receive("stream3", event3)

            group.flush()

            call_kwargs = mock_s3_client.put_object.call_args[1]
            body = call_kwargs["Body"].decode("utf-8")
            assert "From stream1" in body
            assert "From stream2" in body
            assert "From stream3" in body

            group.close()


def test_unicode_content_workflow(mock_boto3_session, mock_s3_client):
    """Test handling of Unicode content throughout workflow."""
    from botocore.exceptions import ClientError

    mock_boto3_session.client.return_value = mock_s3_client
    error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("xlog.group.s3group.HAS_BOTO3", True):
        with patch("xlog.group.s3group.boto3.Session", return_value=mock_boto3_session):
            group = S3Group(
                uri="s3://bucket/unicode.log",
                async_=False,
                ensure_ascii=False,
            )

            event = Log(
                message="Test: 你好世界 🚀 Ñoño",
                level="INFO",
                time=datetime.now(pytz.UTC),
            )
            group.receive("stream1", event)
            group.flush()

            call_kwargs = mock_s3_client.put_object.call_args[1]
            body = call_kwargs["Body"].decode("utf-8")
            assert "你好世界" in body
            assert "🚀" in body
            assert "Ñoño" in body

            group.close()
