import logging
import re
import runpy
from importlib.util import find_spec

import structlog
from rich.text import Span, Text
from richstructlog4 import Logger
from richstructlog4.logger import (
    _checkLevel,
    _LogLevelColumnFormatter,
    _pad,
    _RichKeyValueColumnFormatter,
)


def _flush_richlogger_handlers() -> None:
    stdlib_logger = logging.getLogger("richstructlog4")
    for handler in stdlib_logger.handlers:
        try:
            handler.flush()
        except Exception:
            pass


def test_console_routing_stdout_stderr(capsys):
    structlog.reset_defaults()

    logger = Logger(log_file=None, log_level="DEBUG")

    logger.info("info_out")
    logger.debug("debug_out")
    logger.warning("warn_err")

    captured = capsys.readouterr()

    assert "info_out" in captured.out
    assert "debug_out" in captured.out
    assert "warn_err" not in captured.out

    assert "warn_err" in captured.err
    assert "info_out" not in captured.err


def test_file_logging_is_plain_and_contains_all_levels(tmp_path):
    structlog.reset_defaults()

    log_path = tmp_path / "app.log"
    logger = Logger(log_file=log_path, log_level="DEBUG")

    logger.debug("file_debug")
    logger.warning("file_warn")

    _flush_richlogger_handlers()

    content = log_path.read_text(encoding="utf-8")

    assert "file_debug" in content
    assert "file_warn" in content

    assert "\x1b[" not in content

    assert re.search(r"\blevel=\'?debug\'?", content)
    assert re.search(r"\blevel=\'?warning\'?", content)


def test_check_level_error_paths():
    assert _checkLevel("INFO") == logging.INFO
    assert _checkLevel(logging.DEBUG) == logging.DEBUG

    try:
        _checkLevel("NOPE")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

    try:
        _checkLevel(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError")


def test_formatters_cover_branches():
    logger = Logger(log_file=None)
    console = logger.console

    level_formatter = _LogLevelColumnFormatter(level_styles={}, reset_style="")
    assert "INFO" in level_formatter("level", "info")

    formatter = _RichKeyValueColumnFormatter(
        console=console,
        key_style="k=",
        value_style="v",
        reset_style="r",
        value_repr=str,
        prefix="p",
        postfix="s",
    )

    t = Text("hello", style="bold red")
    t.spans.append(Span(1, 4, "italic"))
    out_text = formatter("msg", t)
    assert "hello" in out_text
    assert "ell" in out_text

    out_markup = formatter("msg", "[bold]hi[/bold]")
    assert "hi" in out_markup

    out_other = formatter("num", 123)
    assert "123" in out_other

    assert _pad("x", 3) == "x  "
    assert Logger._pad("x", 3) == "x  "


def test_warn_fatal_bind_and_close_exception(tmp_path, capsys):
    structlog.reset_defaults()

    class BadCloseHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            return

        def close(self) -> None:
            raise RuntimeError("boom")

    stdlib_logger = logging.getLogger("richstructlog4")
    stdlib_logger.addHandler(BadCloseHandler())

    log_path = tmp_path / "sub" / "app.log"
    logger = Logger(log_file=log_path, log_level="DEBUG")

    logger.bind(user="alice")
    logger.warn("warn_via_warn")
    logger.fatal("fatal_via_fatal")

    captured = capsys.readouterr()
    assert "warn_via_warn" in captured.err
    assert "fatal_via_fatal" in captured.err

    _flush_richlogger_handlers()
    content = log_path.read_text(encoding="utf-8")
    assert "user='alice'" in content or "user=alice" in content


def test_run_as_main_creates_log_file(tmp_path, monkeypatch):
    structlog.reset_defaults()

    monkeypatch.chdir(tmp_path)
    spec = find_spec("richstructlog4.logger")
    assert spec is not None
    assert spec.origin is not None
    runpy.run_path(spec.origin, run_name="__main__")

    log_path = tmp_path / "richstructlog4.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "Starting application" in content
