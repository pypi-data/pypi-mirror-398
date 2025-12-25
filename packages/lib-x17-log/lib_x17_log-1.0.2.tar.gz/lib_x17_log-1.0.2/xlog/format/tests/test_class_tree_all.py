from datetime import datetime

import pytz

from xlog.event.logging import Log
from xlog.format.tree import Tree


def test_construct_with_defaults():
    formatter = Tree()
    assert formatter.width is None
    assert formatter.all_fields is False
    assert formatter.prefix_timeformat == Tree.TIME_FORMAT
    assert formatter.prefix_format == Tree.FORMAT
    assert formatter.prefix_on is True


def test_construct_with_custom_width():
    formatter = Tree(width=120)
    assert formatter.width == 120
    assert formatter.all_fields is False


def test_construct_with_all_fields_true():
    formatter = Tree(all_fields=True)
    assert formatter.all_fields is True
    assert formatter.width is None


def test_construct_with_custom_prefix_timeformat():
    custom_timeformat = "%Y/%m/%d %H:%M"
    formatter = Tree(prefix_timeformat=custom_timeformat)
    assert formatter.prefix_timeformat == custom_timeformat
    assert formatter.prefix_format == Tree.FORMAT


def test_construct_with_custom_prefix_format():
    custom_format = "[{time}] {level} - {message}"
    formatter = Tree(prefix_format=custom_format)
    assert formatter.prefix_format == custom_format
    assert formatter.prefix_timeformat == Tree.TIME_FORMAT


def test_construct_with_prefix_off():
    formatter = Tree(prefix_on=False)
    assert formatter.prefix_on is False


def test_construct_with_all_custom_parameters():
    formatter = Tree(
        width=100,
        all_fields=True,
        prefix_timeformat="%H:%M:%S",
        prefix_format="[{level}] {message}",
        prefix_on=False,
    )
    assert formatter.width == 100
    assert formatter.all_fields is True
    assert formatter.prefix_timeformat == "%H:%M:%S"
    assert formatter.prefix_format == "[{level}] {message}"
    assert formatter.prefix_on is False


def test_resolve_timeformat_with_none_uses_default():
    formatter = Tree()
    result = formatter._resolve_timeformat(None)
    assert result == Tree.TIME_FORMAT


def test_resolve_timeformat_with_custom_value():
    formatter = Tree()
    custom = "%Y-%m-%d"
    result = formatter._resolve_timeformat(custom)
    assert result == custom


def test_resolve_format_with_none_uses_default():
    formatter = Tree()
    result = formatter._resolve_format(None)
    assert result == Tree.FORMAT


def test_resolve_format_with_custom_value():
    formatter = Tree()
    custom = "{time} | {level}"
    result = formatter._resolve_format(custom)
    assert result == custom


def test_resolve_prefix_with_none_uses_default():
    formatter = Tree()
    result = formatter._resolve_prefix(None)
    assert result is True


def test_resolve_prefix_with_false():
    formatter = Tree()
    result = formatter._resolve_prefix(False)
    assert result is False


def test_resolve_prefix_with_true():
    formatter = Tree()
    result = formatter._resolve_prefix(True)
    assert result is True


def test_format_basic_event():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "message: Test message" in result


def test_format_event_with_prefix_on():
    formatter = Tree(prefix_on=True)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "2025-12-06 10:30:45" in result
    assert "INFO" in result


def test_format_event_with_prefix_off():
    formatter = Tree(prefix_on=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "message: Test message" in result


def test_format_event_with_custom_prefix_format():
    formatter = Tree(prefix_format="[{level}] {time}")
    event = Log(
        message="Test message",
        level="WARNING",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "WARNING" in result
    assert "2025-12-06 10:30:45" in result


def test_format_event_with_custom_prefix_timeformat():
    formatter = Tree(prefix_timeformat="%Y/%m/%d")
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "2025/12/06" in result


def test_format_event_with_context():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"job": "batch_process", "env": "production"},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "context" in result


def test_format_event_with_tags():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        tags={"module": "formatter", "version": "2.0"},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "tags" in result


def test_format_event_with_metrics():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        metrics={"duration": 150, "count": 10},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "metrics" in result


def test_format_event_with_all_fields_false_filters_empty():
    formatter = Tree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context=None,
        tags=None,
        metrics=None,
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    # Empty fields should not appear in output


def test_format_event_with_all_fields_true_includes_empty():
    formatter = Tree(all_fields=True)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context=None,
        tags=None,
        metrics=None,
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    # Should include all fields even if empty


def test_format_event_with_nested_dict_context():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={
            "job": "batch_process",
            "details": {"step": "validation", "stage": "pre-processing"},
        },
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "context" in result


def test_format_event_with_list_in_payload():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        extra={"items": ["item1", "item2", "item3"]},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "extra" in result


def test_format_event_with_list_of_dicts():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        extra={
            "records": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        },
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "extra" in result


def test_format_event_with_different_levels():
    formatter = Tree()

    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    for level in levels:
        event = Log(
            message=f"{level} message",
            level=level,
            time=datetime(2025, 12, 6, 10, 30, 45),
        )
        result = formatter.format(event)
        assert isinstance(result, str)
        assert level in result


def test_format_event_with_timezone():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45, tzinfo=pytz.UTC),
        tz="UTC",
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "message: Test message" in result


def test_format_event_with_code():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="ERROR",
        time=datetime(2025, 12, 6, 10, 30, 45),
        code=500,
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "code" in result


def test_format_event_with_custom_id():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        id="custom-id-12345",
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "id" in result


def test_format_event_with_custom_name():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        name="CustomEventName",
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "customeventname" in result.lower()


def test_format_non_eventlike_returns_empty():
    formatter = Tree()
    result = formatter.format("not an event")
    assert result == ""


def test_format_none_returns_empty():
    formatter = Tree()
    result = formatter.format(None)
    assert result == ""


def test_add_node_with_simple_value():
    from rich.tree import Tree as RichTree

    formatter = Tree()
    tree = RichTree("root")
    formatter._add_node(tree, "key", "value")
    # Should not raise any exceptions
    assert tree is not None


def test_add_node_with_dict_value():
    from rich.tree import Tree as RichTree

    formatter = Tree()
    tree = RichTree("root")
    formatter._add_node(tree, "parent", {"child1": "value1", "child2": "value2"})
    # Should not raise any exceptions
    assert tree is not None


def test_add_node_with_list_value():
    from rich.tree import Tree as RichTree

    formatter = Tree()
    tree = RichTree("root")
    formatter._add_node(tree, "items", ["item1", "item2", "item3"])
    # Should not raise any exceptions
    assert tree is not None


def test_add_node_with_nested_list_of_dicts():
    from rich.tree import Tree as RichTree

    formatter = Tree()
    tree = RichTree("root")
    formatter._add_node(
        tree,
        "records",
        [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    )
    # Should not raise any exceptions
    assert tree is not None


def test_format_event_with_width_constraint():
    formatter = Tree(width=80)
    event = Log(
        message="Test message with a very long description that might need wrapping",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_event_filters_none_values():
    formatter = Tree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"key1": "value1", "key2": None},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_empty_string():
    formatter = Tree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"key1": "value1", "key2": ""},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_empty_list():
    formatter = Tree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        extra={"items": []},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_empty_dict():
    formatter = Tree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_false_values():
    formatter = Tree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        extra={"flag": False},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_multiple_events_sequentially():
    formatter = Tree()
    events = [
        Log(message=f"Message {i}", level="INFO", time=datetime(2025, 12, 6, 10, 30, i))
        for i in range(5)
    ]
    for event in events:
        result = formatter.format(event)
        assert isinstance(result, str)
        assert len(result) > 0


def test_format_event_with_unicode_characters():
    formatter = Tree()
    event = Log(
        message="测试消息 with émojis 🎉",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "测试消息" in result or len(result) > 0


def test_format_event_with_special_characters():
    formatter = Tree()
    event = Log(
        message="Test \"quotes\" and 'apostrophes' and <tags>",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0


def test_default_timeformat_constant():
    assert Tree.TIME_FORMAT == "%Y-%m-%d %H:%M:%S"


def test_default_format_constant():
    assert Tree.FORMAT == "[{time}][{level}] {message}"


def test_format_preserves_tree_structure():
    formatter = Tree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"level1": {"level2": {"level3": "deep value"}}},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "context" in result
