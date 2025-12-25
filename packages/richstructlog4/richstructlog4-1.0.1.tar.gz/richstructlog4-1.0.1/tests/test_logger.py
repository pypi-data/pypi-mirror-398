import logging
import re
from io import StringIO

import structlog
from rich.console import Console
from rich.text import Span, Text

from richstructlog4 import Logger
from richstructlog4.logger import (
    _checkLevel,
    _LogLevelColumnFormatter,
    _pad,
    _RichConsoleHandler,
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


def test_console_argument_is_respected_for_output():
    structlog.reset_defaults()

    buf = StringIO()
    console = Console(file=buf, force_terminal=False)
    logger = Logger(log_file=None, log_level="DEBUG", console=console)

    logger.info("hello_console")
    logger.warning("warn_console")

    out = buf.getvalue()
    assert "hello_console" in out
    assert "warn_console" in out


def test_rich_console_handler_handles_formatter_error():
    structlog.reset_defaults()

    buf = StringIO()
    console = Console(file=buf, force_terminal=False)
    logger = Logger(log_file=None, log_level="DEBUG", console=console)

    stdlib_logger = logging.getLogger("richstructlog4")
    handlers = [h for h in stdlib_logger.handlers if isinstance(h, _RichConsoleHandler)]
    assert handlers

    class BadFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            raise RuntimeError("boom")

    for handler in handlers:
        handler.setFormatter(BadFormatter())

    old_raise_exceptions = logging.raiseExceptions
    logging.raiseExceptions = False
    try:
        logger.info("will_not_crash")
    finally:
        logging.raiseExceptions = old_raise_exceptions


def test_rich_console_handler_handles_console_print_error():
    structlog.reset_defaults()

    buf = StringIO()
    console = Console(file=buf, force_terminal=False)
    logger = Logger(log_file=None, log_level="DEBUG", console=console)

    stdlib_logger = logging.getLogger("richstructlog4")
    handlers = [h for h in stdlib_logger.handlers if isinstance(h, _RichConsoleHandler)]
    assert handlers

    class BadConsole:
        def print(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("boom")

    for handler in handlers:
        handler.console = BadConsole()  # type: ignore[assignment]

    old_raise_exceptions = logging.raiseExceptions
    logging.raiseExceptions = False
    try:
        logger.info("will_not_crash")
    finally:
        logging.raiseExceptions = old_raise_exceptions


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
