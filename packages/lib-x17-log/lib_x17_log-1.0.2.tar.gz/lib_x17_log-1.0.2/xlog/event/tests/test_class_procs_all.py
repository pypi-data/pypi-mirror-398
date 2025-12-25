import subprocess
from datetime import datetime

import pytz

from xlog.event.procs import Procs


def test_init_with_successful_process():
    proc = subprocess.CompletedProcess(
        args=["echo", "hello"],
        returncode=0,
        stdout="hello\n",
        stderr="",
    )
    event = Procs(proc=proc)
    assert event.ok is True
    assert event.level == "INFO"
    assert event.code == 0
    assert event.message == "succeed: echo hello"
    assert event.context["status"] == "succeed"
    assert event.context["command"] == "echo hello"
    assert event.context["stdout"] == "hello"
    assert event.context["stderr"] == ""


def test_init_with_failed_process():
    proc = subprocess.CompletedProcess(
        args=["false"],
        returncode=1,
        stdout="",
        stderr="error occurred",
    )
    event = Procs(proc=proc)
    assert event.ok is False
    assert event.level == "ERROR"
    assert event.code == 1
    assert event.message == "failed: false"
    assert event.context["status"] == "failed"
    assert event.context["command"] == "false"
    assert event.context["stdout"] == ""
    assert event.context["stderr"] == "error occurred"


def test_init_with_all_args():
    proc = subprocess.CompletedProcess(
        args=["test", "command"],
        returncode=0,
        stdout="output",
        stderr="",
    )
    now = datetime(2023, 11, 23, 15, 30, 45, tzinfo=pytz.UTC)
    event = Procs(
        proc=proc,
        id="proc123",
        name="TestProcs",
        time=now,
        context={"user": "alice"},
        tags={"env": "prod"},
        metrics={"duration": "100ms"},
        extra={"custom": "data"},
    )
    assert event.id == "proc123"
    assert event.name == "testprocs"
    assert event.time.isoformat() == now.isoformat()
    assert event.context["user"] == "alice"
    assert event.context["status"] == "succeed"
    assert event.tags == {"env": "prod"}
    assert event.metrics == {"duration": "100ms"}
    assert event.extra == {"custom": "data"}


def test_ok_true_for_returncode_zero():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.ok is True


def test_ok_false_for_nonzero_returncode():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
    )
    event = Procs(proc=proc)
    assert event.ok is False


def test_ok_false_for_negative_returncode():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=-1,
    )
    event = Procs(proc=proc)
    assert event.ok is False


def test_level_info_for_success():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.level == "INFO"


def test_level_error_for_failure():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
    )
    event = Procs(proc=proc)
    assert event.level == "ERROR"


def test_status_succeed_for_success():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.context["status"] == "succeed"


def test_status_failed_for_failure():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
    )
    event = Procs(proc=proc)
    assert event.context["status"] == "failed"


def test_code_from_returncode():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=42,
    )
    event = Procs(proc=proc)
    assert event.code == 42


def test_code_none_when_missing():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=None,
    )
    event = Procs(proc=proc)
    assert event.code is None


def test_cmd_with_list_args():
    proc = subprocess.CompletedProcess(
        args=["echo", "hello", "world"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.context["command"] == "echo hello world"


def test_cmd_with_tuple_args():
    proc = subprocess.CompletedProcess(
        args=("ls", "-la", "/tmp"),
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.context["command"] == "ls -la /tmp"


def test_cmd_with_string_args():
    proc = subprocess.CompletedProcess(
        args="echo hello",
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.context["command"] == "echo hello"


def test_message_format_success():
    proc = subprocess.CompletedProcess(
        args=["test", "command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.message == "succeed: test command"


def test_message_format_failure():
    proc = subprocess.CompletedProcess(
        args=["test", "command"],
        returncode=1,
    )
    event = Procs(proc=proc)
    assert event.message == "failed: test command"


def test_stdout_as_string():
    proc = subprocess.CompletedProcess(
        args=["echo", "test"],
        returncode=0,
        stdout="test output\n",
    )
    event = Procs(proc=proc)
    assert event.context["stdout"] == "test output"


def test_stdout_as_bytes():
    proc = subprocess.CompletedProcess(
        args=["echo", "test"],
        returncode=0,
        stdout=b"test output\n",
    )
    event = Procs(proc=proc)
    assert event.context["stdout"] == "test output"


def test_stdout_with_whitespace_stripped():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="  output with spaces  \n\n",
    )
    event = Procs(proc=proc)
    assert event.context["stdout"] == "output with spaces"


def test_stdout_empty():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="",
    )
    event = Procs(proc=proc)
    assert event.context["stdout"] == ""


def test_stdout_missing():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.context["stdout"] == ""


def test_stderr_as_string():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
        stderr="error message\n",
    )
    event = Procs(proc=proc)
    assert event.context["stderr"] == "error message"


def test_stderr_as_bytes():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
        stderr=b"error message\n",
    )
    event = Procs(proc=proc)
    assert event.context["stderr"] == "error message"


def test_stderr_with_whitespace_stripped():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
        stderr="  error  \n",
    )
    event = Procs(proc=proc)
    assert event.context["stderr"] == "error"


def test_stderr_empty():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stderr="",
    )
    event = Procs(proc=proc)
    assert event.context["stderr"] == ""


def test_stderr_missing():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.context["stderr"] == ""


def test_stdout_truncated_when_long():
    long_output = "x" * 2000
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout=long_output,
    )
    event = Procs(proc=proc)
    assert len(event.context["stdout"]) == Procs.TRUNCATE
    assert event.context["stdout"] == "x" * Procs.TRUNCATE


def test_stderr_truncated_when_long():
    long_error = "y" * 2000
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
        stderr=long_error,
    )
    event = Procs(proc=proc)
    assert len(event.context["stderr"]) == Procs.TRUNCATE
    assert event.context["stderr"] == "y" * Procs.TRUNCATE


def test_truncate_constant():
    assert Procs.TRUNCATE == 1000


def test_stdout_with_unicode():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="Hello 世界 🌍",
    )
    event = Procs(proc=proc)
    assert event.context["stdout"] == "Hello 世界 🌍"


def test_stdout_bytes_with_invalid_utf8():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout=b"Hello\xff\xfeWorld",
    )
    event = Procs(proc=proc)
    # Should not raise an error, uses 'replace' error handling
    assert isinstance(event.context["stdout"], str)


def test_equality_with_same_process():
    proc1 = subprocess.CompletedProcess(
        args=["echo", "test"],
        returncode=0,
        stdout="test",
        stderr="",
    )
    proc2 = subprocess.CompletedProcess(
        args=["echo", "test"],
        returncode=0,
        stdout="test",
        stderr="",
    )
    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    assert event1 == event2


def test_equality_with_different_args():
    proc1 = subprocess.CompletedProcess(
        args=["echo", "test1"],
        returncode=0,
        stdout="test1",
        stderr="",
    )
    proc2 = subprocess.CompletedProcess(
        args=["echo", "test2"],
        returncode=0,
        stdout="test2",
        stderr="",
    )
    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    assert event1 != event2


def test_equality_with_different_returncode():
    proc1 = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="",
        stderr="",
    )
    proc2 = subprocess.CompletedProcess(
        args=["command"],
        returncode=1,
        stdout="",
        stderr="",
    )
    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    assert event1 != event2


def test_equality_with_different_stdout():
    proc1 = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="output1",
        stderr="",
    )
    proc2 = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="output2",
        stderr="",
    )
    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    assert event1 != event2


def test_equality_with_different_stderr():
    proc1 = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="",
        stderr="error1",
    )
    proc2 = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="",
        stderr="error2",
    )
    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    assert event1 != event2


def test_equality_with_dict():
    proc = subprocess.CompletedProcess(
        args=["echo", "test"],
        returncode=0,
        stdout="test",
        stderr="",
    )
    event = Procs(proc=proc)
    event_dict = event.to_dict()
    assert isinstance(event_dict, dict)


def test_equality_with_other_type():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event != 123
    assert event != ["list"]
    assert event != "string"


def test_not_equal_operator():
    proc1 = subprocess.CompletedProcess(
        args=["command1"],
        returncode=0,
    )
    proc2 = subprocess.CompletedProcess(
        args=["command2"],
        returncode=0,
    )
    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    assert event1 != event2


def test_context_includes_additional_fields():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="output",
        stderr="",
    )
    event = Procs(
        proc=proc,
        context={"user": "alice", "environment": "prod"},
    )
    assert event.context["user"] == "alice"
    assert event.context["environment"] == "prod"
    assert event.context["status"] == "succeed"
    assert event.context["command"] == "command"
    assert event.context["stdout"] == "output"
    assert event.context["stderr"] == ""


def test_to_dict():
    proc = subprocess.CompletedProcess(
        args=["test", "command"],
        returncode=0,
        stdout="output",
        stderr="",
    )
    event = Procs(proc=proc, id="proc123", name="test")
    result = event.to_dict()
    assert result["id"] == "proc123"
    assert result["name"] == "test"
    assert result["message"] == "succeed: test command"
    assert result["level"] == "INFO"
    assert result["code"] == 0
    assert result["context"]["status"] == "succeed"
    assert result["context"]["command"] == "test command"


def test_describe():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="output",
        stderr="",
    )
    event = Procs(proc=proc)
    result = event.describe()
    assert isinstance(result, dict)
    assert result["message"] == "succeed: command"
    assert result["level"] == "INFO"
    assert result["context"]["status"] == "succeed"


def test_inherits_from_base_event():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert hasattr(event, "ensure_serialisable")
    assert hasattr(event, "LEVELS")
    assert hasattr(event, "to_dict")
    assert hasattr(event, "describe")
    assert hasattr(event, "get")


def test_get_existing_attribute():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.get("level") == "INFO"
    assert event.get("ok") is True


def test_get_nonexistent_attribute():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.get("nonexistent") is None


def test_get_with_default():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
    )
    event = Procs(proc=proc)
    assert event.get("nonexistent", "default") == "default"


def test_proc_attribute_accessible():
    proc = subprocess.CompletedProcess(
        args=["command"],
        returncode=0,
        stdout="output",
    )
    event = Procs(proc=proc)
    assert event.proc is proc
    assert event.proc.args == ["command"]
    assert event.proc.returncode == 0


def test_multiple_procs_with_different_processes():
    proc1 = subprocess.CompletedProcess(args=["cmd1"], returncode=0)
    proc2 = subprocess.CompletedProcess(args=["cmd2"], returncode=1)
    proc3 = subprocess.CompletedProcess(args=["cmd3"], returncode=0)

    event1 = Procs(proc=proc1)
    event2 = Procs(proc=proc2)
    event3 = Procs(proc=proc3)

    assert event1.ok is True
    assert event2.ok is False
    assert event3.ok is True
    assert event1.id != event2.id
    assert event2.id != event3.id


def test_real_world_git_command_success():
    proc = subprocess.CompletedProcess(
        args=["git", "status"],
        returncode=0,
        stdout="On branch main\nnothing to commit, working tree clean\n",
        stderr="",
    )
    event = Procs(proc=proc)
    assert event.ok is True
    assert event.level == "INFO"
    assert event.message == "succeed: git status"
    assert "On branch main" in event.context["stdout"]


def test_real_world_command_failure():
    proc = subprocess.CompletedProcess(
        args=["ls", "/nonexistent/path"],
        returncode=1,
        stdout="",
        stderr="ls: cannot access '/nonexistent/path': No such file or directory",
    )
    event = Procs(proc=proc)
    assert event.ok is False
    assert event.level == "ERROR"
    assert event.message == "failed: ls /nonexistent/path"
    assert "No such file or directory" in event.context["stderr"]


def test_complex_command_with_args():
    proc = subprocess.CompletedProcess(
        args=["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        returncode=0,
        stdout="collected 10 items\nall tests passed",
        stderr="",
    )
    event = Procs(proc=proc)
    assert event.ok is True
    assert event.context["command"] == "python -m pytest tests/ -v --tb=short"
    assert "all tests passed" in event.context["stdout"]
