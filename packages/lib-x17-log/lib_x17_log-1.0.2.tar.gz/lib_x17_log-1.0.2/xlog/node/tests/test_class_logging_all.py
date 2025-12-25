import logging
import threading

import pytest

from xlog.node.logging import Logging


def _count_x17_handlers(logger: logging.Logger) -> int:
    return sum(1 for h in logger.handlers if getattr(h, "_x17", False))


def _count_foreign_handlers(logger: logging.Logger) -> int:
    return sum(1 for h in logger.handlers if not getattr(h, "_x17", False))


def test_logger_creation():
    node = Logging(name="testnode", verbose=True)
    assert isinstance(node.node, logging.Logger)
    assert node.node.name == "testnode"


def test_verbose_adds_handler_once():
    node = Logging(name="vnode", verbose=True)
    handlers = node.node.handlers
    assert len(handlers) == 1
    assert getattr(handlers[0], "_x17", False) is True

    node2 = Logging(name="vnode", verbose=True)
    handlers2 = node2.node.handlers
    assert len(handlers2) == 1
    assert getattr(handlers2[0], "_x17", False) is True


def test_verbose_false_has_no_handler():
    node = Logging(name="silentnode", verbose=False)
    assert node.node.handlers == []


def test_level_setting():
    node = Logging(name="levelnode", level="ERROR")
    assert node.node.level == logging.ERROR

    node2 = Logging(name="levelnode2", level="warning")
    assert node2.node.level == logging.WARNING


def test_log_does_not_crash():
    node = Logging(name="logtest", verbose=True, level="INFO")
    try:
        node.info("hello world")
        node.error("something wrong")
        node.debug("debug msg")
    except Exception as e:
        pytest.fail(f"log() raised exception: {e}")


def test_multiple_nodes_different_ids():
    n1 = Logging(name="aaa", verbose=True)
    n2 = Logging(name="bbb", verbose=True)
    assert n1.name == "aaa"
    assert n2.name == "bbb"
    assert n1.node is not n2.node


def test_handler_owned_detection():
    node = Logging(name="foreign", verbose=False)
    h = logging.StreamHandler()
    node.node.addHandler(h)
    node2 = Logging(name="foreign", verbose=True)
    x17_handlers = [h for h in node2.node.handlers if getattr(h, "_x17", False)]
    assert len(x17_handlers) == 1


def test_logger_basic_identity():
    node = Logging(name="basic", verbose=True)
    assert isinstance(node.node, logging.Logger)
    assert node.node.name == "basic"
    assert node.name == "basic"


def test_default_name_is_id_lowercase():
    node = Logging(verbose=True)
    assert isinstance(node.name, str)
    assert len(node.name) > 0
    assert node.name == node.name.lower()


def test_level_resolution_accepts_case_insensitive():
    n1 = Logging(name="lvl1", level="ERROR", verbose=False)
    assert n1.node.level == logging.ERROR

    n2 = Logging(name="lvl2", level="warning", verbose=False)
    assert n2.node.level == logging.WARNING

    n3 = Logging(name="lvl3", level="notalevel", verbose=False)
    assert n3.node.level == logging.INFO


def test_verbose_true_adds_one_x17_handler_only():
    node1 = Logging(name="vtrue", verbose=True)
    assert _count_x17_handlers(node1.node) == 1

    node2 = Logging(name="vtrue", verbose=True)
    assert _count_x17_handlers(node2.node) == 1
    assert len(node2.node.handlers) == len(node1.node.handlers)


def test_verbose_false_adds_no_handler():
    node = Logging(name="vfalse", verbose=False)
    assert len(node.node.handlers) == 0


def test_foreign_handler_does_not_block_x17_handler():
    node0 = Logging(name="foreign_block", verbose=False)
    foreign = logging.StreamHandler()
    node0.node.addHandler(foreign)
    assert _count_foreign_handlers(node0.node) == 1
    assert _count_x17_handlers(node0.node) == 0

    node1 = Logging(name="foreign_block", verbose=True)
    assert _count_x17_handlers(node1.node) == 1
    assert _count_foreign_handlers(node1.node) == 1


def test_existing_x17_handler_prevents_duplicates_even_with_foreign():
    node0 = Logging(name="foreign_mix", verbose=True)
    assert _count_x17_handlers(node0.node) == 1

    foreign = logging.StreamHandler()
    node0.node.addHandler(foreign)
    assert _count_foreign_handlers(node0.node) == 1

    node1 = Logging(name="foreign_mix", verbose=True)
    assert _count_x17_handlers(node1.node) == 1
    assert _count_foreign_handlers(node1.node) == 1


def test_propagate_flag_is_respected():
    node = Logging(name="prop", verbose=False, propagate=True)
    assert node.node.propagate is True

    node2 = Logging(name="prop2", verbose=False, propagate=False)
    assert node2.node.propagate is False


def test_log_methods_do_not_crash():
    node = Logging(name="sugar", verbose=True)
    node.info("i")
    node.warning("w")
    node.error("e")
    node.debug("d")


def test_extra_passthrough_does_not_crash():
    node = Logging(name="extra", verbose=True)
    node.info("hello", extra={"event": {"a": 1}})
    node.log("INFO", "hello2", extra={"x": 2})


def test_really_emits_to_stderr(capsys):
    node = Logging(name="emit", verbose=True, level="INFO")
    node.info("hello world")

    captured = capsys.readouterr()
    assert "hello world" in captured.err
    assert captured.err.strip().endswith("hello world")


def test_level_filtering_effect(capsys):
    node = Logging(name="filter", verbose=True, level="ERROR")
    node.info("should_not_show")
    node.error("should_show")
    captured = capsys.readouterr()
    assert "should_show" in captured.err
    assert "should_not_show" not in captured.err


def test_thread_safety_no_duplicate_x17_handlers():
    name = "threaded"

    def worker():
        Logging(name=name, verbose=True)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    logger = logging.getLogger(name)
    assert _count_x17_handlers(logger) == 1


def test_logger_name_is_reused_global_singleton():
    n1 = Logging(name="singleton", verbose=False)
    n2 = Logging(name="singleton", verbose=False)
    assert n1.node is n2.node
