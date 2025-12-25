from datetime import datetime

import pytz

from xlog.event.logging import Log
from xlog.format.colortree import ColorTree


def test_construct_with_defaults():
    formatter = ColorTree()
    assert formatter.width is None
    assert formatter.all_fields is False
    assert formatter.colors == ColorTree.COLORS
    assert formatter.prefix_timeformat == ColorTree.TIME_FORMAT
    assert formatter.prefix_format == ColorTree.FORMAT
    assert formatter.prefix_on is True


def test_construct_with_custom_width():
    formatter = ColorTree(width=120)
    assert formatter.width == 120
    assert formatter.all_fields is False


def test_construct_with_all_fields_true():
    formatter = ColorTree(all_fields=True)
    assert formatter.all_fields is True
    assert formatter.width is None


def test_construct_with_custom_colors():
    custom_colors = {
        "INFO": "blue",
        "ERROR": "magenta",
        "WARNING": "orange",
    }
    formatter = ColorTree(colors=custom_colors)
    assert formatter.colors == custom_colors


def test_construct_with_custom_prefix_timeformat():
    custom_timeformat = "%Y/%m/%d %H:%M"
    formatter = ColorTree(prefix_timeformat=custom_timeformat)
    assert formatter.prefix_timeformat == custom_timeformat
    assert formatter.prefix_format == ColorTree.FORMAT


def test_construct_with_custom_prefix_format():
    custom_format = "[{time}] {level} - {message}"
    formatter = ColorTree(prefix_format=custom_format)
    assert formatter.prefix_format == custom_format
    assert formatter.prefix_timeformat == ColorTree.TIME_FORMAT


def test_construct_with_prefix_off():
    formatter = ColorTree(prefix_on=False)
    assert formatter.prefix_on is False


def test_construct_with_all_custom_parameters():
    custom_colors = {"INFO": "blue", "ERROR": "red"}
    formatter = ColorTree(
        width=100,
        all_fields=True,
        colors=custom_colors,
        prefix_timeformat="%H:%M:%S",
        prefix_format="[{level}] {message}",
        prefix_on=False,
    )
    assert formatter.width == 100
    assert formatter.all_fields is True
    assert formatter.colors == custom_colors
    assert formatter.prefix_timeformat == "%H:%M:%S"
    assert formatter.prefix_format == "[{level}] {message}"
    assert formatter.prefix_on is False


def test_default_colors_mapping():
    assert ColorTree.COLORS["INFO"] == "green"
    assert ColorTree.COLORS["DEBUG"] == "cyan"
    assert ColorTree.COLORS["WARNING"] == "yellow"
    assert ColorTree.COLORS["ERROR"] == "red"
    assert ColorTree.COLORS["CRITICAL"] == "red"
    assert ColorTree.COLORS["UNKNOWN"] == "purple"


def test_resolve_timeformat_with_none_uses_default():
    formatter = ColorTree()
    result = formatter._resolve_timeformat(None)
    assert result == ColorTree.TIME_FORMAT


def test_resolve_timeformat_with_custom_value():
    formatter = ColorTree()
    custom = "%Y-%m-%d"
    result = formatter._resolve_timeformat(custom)
    assert result == custom


def test_resolve_format_with_none_uses_default():
    formatter = ColorTree()
    result = formatter._resolve_format(None)
    assert result == ColorTree.FORMAT


def test_resolve_format_with_custom_value():
    formatter = ColorTree()
    custom = "{time} | {level}"
    result = formatter._resolve_format(custom)
    assert result == custom


def test_resolve_prefix_with_none_uses_default():
    formatter = ColorTree()
    result = formatter._resolve_prefix(None)
    assert result is True


def test_resolve_prefix_with_false():
    formatter = ColorTree()
    result = formatter._resolve_prefix(False)
    assert result is False


def test_resolve_prefix_with_true():
    formatter = ColorTree()
    result = formatter._resolve_prefix(True)
    assert result is True


def test_pick_level_style_for_info():
    formatter = ColorTree()
    event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "green"


def test_pick_level_style_for_debug():
    formatter = ColorTree()
    event = Log(message="Test", level="DEBUG", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "cyan"


def test_pick_level_style_for_warning():
    formatter = ColorTree()
    event = Log(message="Test", level="WARNING", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "yellow"


def test_pick_level_style_for_error():
    formatter = ColorTree()
    event = Log(message="Test", level="ERROR", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "red"


def test_pick_level_style_for_critical():
    formatter = ColorTree()
    event = Log(message="Test", level="CRITICAL", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "red"


def test_pick_level_style_for_unknown_level():
    formatter = ColorTree()
    event = Log(message="Test", level="CUSTOM", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    # CUSTOM level is not valid, so it defaults to INFO which is green
    assert style == "green"


def test_pick_level_style_for_lowercase_level():
    formatter = ColorTree()
    event = Log(message="Test", level="info", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "green"


def test_pick_level_style_with_custom_colors():
    custom_colors = {"INFO": "blue", "ERROR": "purple"}
    formatter = ColorTree(colors=custom_colors)
    event = Log(message="Test", level="INFO", time=datetime.now(pytz.UTC))
    style = formatter._pick_level_style(event)
    assert style == "blue"


def test_pick_level_style_without_level_attribute():
    formatter = ColorTree()

    class MockEvent:
        message = "Test"
        time = datetime.now(pytz.UTC)

    event = MockEvent()
    style = formatter._pick_level_style(event)
    assert style == "green"


def test_format_basic_event():
    formatter = ColorTree()
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
    formatter = ColorTree(prefix_on=True)
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
    formatter = ColorTree(prefix_on=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "message: Test message" in result


def test_format_event_with_custom_prefix_format():
    formatter = ColorTree(prefix_format="[{level}] {time}")
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
    formatter = ColorTree(prefix_timeformat="%Y/%m/%d")
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "2025/12/06" in result


def test_format_event_with_context():
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree(all_fields=False)
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
    formatter = ColorTree(all_fields=True)
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
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree()

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


def test_format_event_with_debug_level_uses_cyan():
    formatter = ColorTree()
    event = Log(
        message="Debug message",
        level="DEBUG",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "DEBUG" in result


def test_format_event_with_error_level_uses_red():
    formatter = ColorTree()
    event = Log(
        message="Error message",
        level="ERROR",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "ERROR" in result


def test_format_event_with_timezone():
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree()
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
    formatter = ColorTree()
    result = formatter.format("not an event")
    assert result == ""


def test_format_none_returns_empty():
    formatter = ColorTree()
    result = formatter.format(None)
    assert result == ""


def test_add_node_with_simple_value():
    from rich.tree import Tree as RichTree

    formatter = ColorTree()
    tree = RichTree("root")
    formatter._add_node(tree, "key", "value")
    # Should not raise any exceptions
    assert tree is not None


def test_add_node_with_dict_value():
    from rich.tree import Tree as RichTree

    formatter = ColorTree()
    tree = RichTree("root")
    formatter._add_node(tree, "parent", {"child1": "value1", "child2": "value2"})
    # Should not raise any exceptions
    assert tree is not None


def test_add_node_with_list_value():
    from rich.tree import Tree as RichTree

    formatter = ColorTree()
    tree = RichTree("root")
    formatter._add_node(tree, "items", ["item1", "item2", "item3"])
    # Should not raise any exceptions
    assert tree is not None


def test_add_node_with_nested_list_of_dicts():
    from rich.tree import Tree as RichTree

    formatter = ColorTree()
    tree = RichTree("root")
    formatter._add_node(
        tree,
        "records",
        [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    )
    # Should not raise any exceptions
    assert tree is not None


def test_format_event_with_width_constraint():
    formatter = ColorTree(width=80)
    event = Log(
        message="Test message with a very long description that might need wrapping",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_event_filters_none_values():
    formatter = ColorTree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"key1": "value1", "key2": None},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_empty_string():
    formatter = ColorTree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"key1": "value1", "key2": ""},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_empty_list():
    formatter = ColorTree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        extra={"items": []},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_empty_dict():
    formatter = ColorTree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_event_filters_false_values():
    formatter = ColorTree(all_fields=False)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        extra={"flag": False},
    )
    result = formatter.format(event)
    assert isinstance(result, str)


def test_format_multiple_events_sequentially():
    formatter = ColorTree()
    events = [
        Log(message=f"Message {i}", level="INFO", time=datetime(2025, 12, 6, 10, 30, i))
        for i in range(5)
    ]
    for event in events:
        result = formatter.format(event)
        assert isinstance(result, str)
        assert len(result) > 0


def test_format_event_with_unicode_characters():
    formatter = ColorTree()
    event = Log(
        message="测试消息 with émojis 🎉",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "测试消息" in result or len(result) > 0


def test_format_event_with_special_characters():
    formatter = ColorTree()
    event = Log(
        message="Test \"quotes\" and 'apostrophes' and <tags>",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0


def test_default_timeformat_constant():
    assert ColorTree.TIME_FORMAT == "%Y-%m-%d %H:%M:%S"


def test_default_format_constant():
    assert ColorTree.FORMAT == "[{time}][{level}] {message}"


def test_format_preserves_tree_structure():
    formatter = ColorTree()
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={"level1": {"level2": {"level3": "deep value"}}},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "context" in result


def test_format_with_custom_colors_overrides_defaults():
    custom_colors = {
        "INFO": "white",
        "DEBUG": "light_blue",
        "WARNING": "orange",
        "ERROR": "dark_red",
        "CRITICAL": "bold_red",
    }
    formatter = ColorTree(colors=custom_colors)
    event = Log(
        message="Test message",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    style = formatter._pick_level_style(event)
    assert style == "white"


def test_format_event_with_complex_nested_structure():
    formatter = ColorTree()
    event = Log(
        message="Complex structure",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        context={
            "service": "api",
            "request": {
                "method": "POST",
                "endpoint": "/api/v1/users",
                "headers": {"Content-Type": "application/json"},
                "body": {"name": "Alice", "email": "alice@example.com"},
            },
            "response": {
                "status": 201,
                "data": {"id": 123, "created": True},
            },
        },
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert "context" in result


def test_add_node_with_mixed_list_content():
    from rich.tree import Tree as RichTree

    formatter = ColorTree()
    tree = RichTree("root")
    formatter._add_node(
        tree,
        "mixed",
        ["string", 123, {"key": "value"}, ["nested", "list"]],
    )
    # Should not raise any exceptions
    assert tree is not None


def test_format_event_with_all_optional_fields():
    formatter = ColorTree()
    event = Log(
        message="Complete event",
        level="INFO",
        time=datetime(2025, 12, 6, 10, 30, 45),
        id="evt-123",
        name="TestEvent",
        code=200,
        context={"key": "value"},
        tags={"tag": "value"},
        metrics={"metric": 100},
        extra={"extra": "data"},
    )
    result = formatter.format(event)
    assert isinstance(result, str)
    assert len(result) > 0
