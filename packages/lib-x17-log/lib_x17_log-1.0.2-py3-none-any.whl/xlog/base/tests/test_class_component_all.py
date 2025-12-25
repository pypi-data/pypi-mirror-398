from datetime import date, datetime, time, timedelta

from xlog.base.component import LogComponent


def test_init_with_id_and_name():
    component = LogComponent(id="test123", name="TestComponent")
    assert component.id == "test123"
    assert component.name == "testcomponent"


def test_init_with_id_only():
    component = LogComponent(id="test456")
    assert component.id == "test456"
    assert component.name == "test456"


def test_init_with_name_only():
    component = LogComponent(name="MyLogger")
    assert component.name == "mylogger"
    assert len(component.id) == 10


def test_init_with_no_args():
    component = LogComponent()
    assert len(component.id) == 10
    assert component.name == component.id


def test_name_is_lowercase():
    component = LogComponent(name="UpperCaseNAME")
    assert component.name == "uppercasename"


def test_levels_constant():
    assert "DEBUG" in LogComponent.LEVELS
    assert "WARNING" in LogComponent.LEVELS
    assert "INFO" in LogComponent.LEVELS
    assert "ERROR" in LogComponent.LEVELS
    assert "UNKNOWN" in LogComponent.LEVELS
    assert "CRITICAL" in LogComponent.LEVELS


def test_ensure_serialisable_primitives():
    assert LogComponent.ensure_serialisable("string") == "string"
    assert LogComponent.ensure_serialisable(42) == 42
    assert LogComponent.ensure_serialisable(3.14) == 3.14
    assert LogComponent.ensure_serialisable(True) is True
    assert LogComponent.ensure_serialisable(None) is None


def test_ensure_serialisable_datetime():
    dt = datetime(2023, 11, 23, 15, 30, 45)
    result = LogComponent.ensure_serialisable(dt)
    assert result == "2023-11-23T15:30:45"


def test_ensure_serialisable_date():
    d = date(2023, 11, 23)
    result = LogComponent.ensure_serialisable(d)
    assert result == "2023-11-23"


def test_ensure_serialisable_time():
    t = time(15, 30, 45)
    result = LogComponent.ensure_serialisable(t)
    assert result == "15:30:45"


def test_ensure_serialisable_timedelta():
    td = timedelta(days=2, hours=3, minutes=15)
    result = LogComponent.ensure_serialisable(td)
    assert result == "2 days, 3:15:00"


def test_ensure_serialisable_dict():
    data = {
        "name": "test",
        "count": 42,
        "timestamp": datetime(2023, 11, 23, 12, 0, 0),
    }
    result = LogComponent.ensure_serialisable(data)
    assert result["name"] == "test"
    assert result["count"] == 42
    assert result["timestamp"] == "2023-11-23T12:00:00"


def test_ensure_serialisable_nested_dict():
    data = {
        "outer": {
            "inner": {
                "value": 123,
                "date": date(2023, 11, 23),
            }
        }
    }
    result = LogComponent.ensure_serialisable(data)
    assert result["outer"]["inner"]["value"] == 123
    assert result["outer"]["inner"]["date"] == "2023-11-23"


def test_ensure_serialisable_list():
    data = [1, "string", datetime(2023, 11, 23, 10, 0, 0), True]
    result = LogComponent.ensure_serialisable(data)
    assert result[0] == 1
    assert result[1] == "string"
    assert result[2] == "2023-11-23T10:00:00"
    assert result[3] is True


def test_ensure_serialisable_tuple():
    data = (1, "test", date(2023, 11, 23))
    result = LogComponent.ensure_serialisable(data)
    assert isinstance(result, list)
    assert result[0] == 1
    assert result[1] == "test"
    assert result[2] == "2023-11-23"


def test_ensure_serialisable_set():
    data = {1, 2, 3}
    result = LogComponent.ensure_serialisable(data)
    assert isinstance(result, list)
    assert sorted(result) == [1, 2, 3]


def test_ensure_serialisable_custom_object():
    class CustomClass:
        def __str__(self):
            return "custom_value"

    obj = CustomClass()
    result = LogComponent.ensure_serialisable(obj)
    assert result == "custom_value"


def test_ensure_serialisable_complex_structure():
    data = {
        "users": [
            {"name": "Alice", "joined": datetime(2023, 1, 1, 0, 0, 0)},
            {"name": "Bob", "joined": datetime(2023, 6, 15, 0, 0, 0)},
        ],
        "metadata": {
            "created": date(2023, 11, 23),
            "duration": timedelta(hours=5),
        },
    }
    result = LogComponent.ensure_serialisable(data)
    assert result["users"][0]["name"] == "Alice"
    assert result["users"][0]["joined"] == "2023-01-01T00:00:00"
    assert result["users"][1]["name"] == "Bob"
    assert result["metadata"]["created"] == "2023-11-23"
    assert result["metadata"]["duration"] == "5:00:00"


def test_resolve_struct_with_none():
    component = LogComponent()
    result = component._resolve_struct(None)
    assert result == {}


def test_resolve_struct_with_dict():
    component = LogComponent()
    data = {"key": "value", "timestamp": datetime(2023, 11, 23, 10, 0, 0)}
    result = component._resolve_struct(data)
    assert result["key"] == "value"
    assert result["timestamp"] == "2023-11-23T10:00:00"


def test_str_representation():
    component = LogComponent(name="TestLogger")
    assert str(component) == "testlogger"


def test_repr_representation():
    component = LogComponent(id="abc123", name="TestLogger")
    result = repr(component)
    assert "LogComponent" in result
    assert "id=abc123" in result
    assert "name=testlogger" in result


def test_multiple_components_have_unique_ids():
    component1 = LogComponent()
    component2 = LogComponent()
    component3 = LogComponent()
    assert component1.id != component2.id
    assert component2.id != component3.id
    assert component1.id != component3.id
