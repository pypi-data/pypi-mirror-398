from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Callable, Literal

import structlog
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.text import Text
from structlog.typing import Processor

AcceptableLevel = Literal[
    "NOTSET", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL"
]


def _pad(s: str, length: int) -> str:
    missing = length - len(s)

    return s + " " * (missing if missing > 0 else 0)


def _checkLevel(level: int | AcceptableLevel) -> int:
    if isinstance(level, int):
        rv = level
    elif str(level) == level:
        if level not in logging._nameToLevel:
            raise ValueError(f"Unknown level: {level}")
        rv = logging._nameToLevel[level]
    else:
        raise TypeError(f"Level not an integer or a valid string: {level}")

    return rv


class _LessThanLevelFilter(logging.Filter):
    def __init__(self, max_exclusive: int) -> None:
        super().__init__()
        self.max_exclusive = max_exclusive

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_exclusive


class _GreaterEqualLevelFilter(logging.Filter):
    def __init__(self, min_inclusive: int) -> None:
        super().__init__()
        self.min_inclusive = min_inclusive

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.min_inclusive


class _LogLevelColumnFormatter:
    level_styles: dict[str, str] | None
    reset_style: str
    width: int

    def __init__(self, level_styles: dict[str, str], reset_style: str) -> None:
        self.level_styles = level_styles
        if level_styles:
            self.width = len(max(self.level_styles.keys(), key=lambda e: len(e)))
            self.reset_style = reset_style
        else:
            self.width = 0
            self.reset_style = ""

    def __call__(self, key: str, value: object) -> str:
        level = str(value)
        style = "" if self.level_styles is None else self.level_styles.get(level, "")

        return f"{style}{_pad(level.upper(), self.width)}{self.reset_style}"


@dataclass
class _RichKeyValueColumnFormatter:
    console: Console
    key_style: str | None
    value_style: str
    reset_style: str
    value_repr: Callable[[object], str]
    width: int = 0
    prefix: str = ""
    postfix: str = ""

    highlighter = ReprHighlighter()

    def __call__(self, key: str, value: object) -> str:
        sio = StringIO()

        if self.prefix:
            sio.write(self.prefix)
            sio.write(self.reset_style)

        if self.key_style is not None:
            sio.write(self.key_style)
            sio.write(key)
            sio.write(self.reset_style)
            sio.write("=")

        if isinstance(value, Text):
            style = Style.parse(value.style) if isinstance(value.style, str) else value.style
            sio.write(style.render(value._text[0]))
            for span in value.spans:
                style = Style.parse(span.style) if isinstance(span.style, str) else span.style
                sio.write(style.render(value.plain[span.start : span.end]))
        elif isinstance(value, str):
            for segment1 in Text.from_markup(value).render(self.console):
                if segment1.style is not None and segment1.style.__bool__():
                    sio.write(segment1.style.render(segment1.text))
                    continue

                for segment2 in self.highlighter(segment1.text).render(self.console):
                    sio.write(
                        segment2.text
                        if segment2.style is None
                        else segment2.style.render(segment2.text)
                    )
        else:
            sio.write(self.value_style)
            sio.write(_pad(self.value_repr(value), self.width))
            sio.write(self.reset_style)

        if self.postfix:
            sio.write(self.postfix)
            sio.write(self.reset_style)

        return sio.getvalue()


class Logger:
    @staticmethod
    def _pad(s: str, length: int) -> str:
        return _pad(s, length)

    def __init__(
        self,
        log_file: str | Path | None = None,
        log_level: int | AcceptableLevel = logging.INFO,
        console: Console | None = None,
    ) -> None:
        self.console = Console() if console is None else console
        levelno = _checkLevel(log_level)

        logger_name = "richstructlog4"
        stdlib_logger = logging.getLogger(logger_name)
        for handler in stdlib_logger.handlers[:]:
            stdlib_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
        stdlib_logger.propagate = False
        stdlib_logger.setLevel(levelno)

        foreign_pre_chain: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        ]

        console_renderer = structlog.dev.ConsoleRenderer(
            columns=[
                structlog.dev.Column(
                    "timestamp",
                    structlog.dev.KeyValueColumnFormatter(
                        key_style=None,
                        value_style="\033[2;36m",
                        reset_style="\033[0m",
                        value_repr=str,
                    ),
                ),
                structlog.dev.Column(
                    "level",
                    _LogLevelColumnFormatter(
                        level_styles={
                            "critical": "\033[7;1;31m",
                            "exception": "\033[1;31m",
                            "error": "\033[1;31m",
                            "warn": "\033[1;33m",
                            "warning": "\033[1;33m",
                            "info": "\033[34m",
                            "debug": "\033[2;34m",
                            "notset": "\033[2m",
                        },
                        reset_style="\033[0m",
                    ),
                ),
                structlog.dev.Column(
                    "event",
                    _RichKeyValueColumnFormatter(
                        console=self.console,
                        key_style=None,
                        value_style="\033[37m",
                        reset_style="\033[0m",
                        value_repr=str,
                    ),
                ),
                structlog.dev.Column(
                    "",
                    structlog.dev.KeyValueColumnFormatter(
                        key_style="\033[36m",
                        value_style="\033[35m",
                        reset_style="\033[0m",
                        value_repr=str,
                    ),
                ),
            ]
        )

        console_formatter = structlog.stdlib.ProcessorFormatter(
            processor=console_renderer,
            foreign_pre_chain=foreign_pre_chain,
        )

        file_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.KeyValueRenderer(
                key_order=["timestamp", "level", "event"],
                sort_keys=True,
            ),
            foreign_pre_chain=foreign_pre_chain,
        )

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.addFilter(_LessThanLevelFilter(logging.WARNING))
        stdout_handler.setLevel(levelno)
        stdout_handler.setFormatter(console_formatter)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.addFilter(_GreaterEqualLevelFilter(logging.WARNING))
        stderr_handler.setLevel(levelno)
        stderr_handler.setFormatter(console_formatter)

        stdlib_logger.addHandler(stdout_handler)
        stdlib_logger.addHandler(stderr_handler)

        if log_file is not None:
            log_path = Path(log_file)
            if log_path.parent != Path("."):
                log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(levelno)
            file_handler.setFormatter(file_formatter)
            stdlib_logger.addHandler(file_handler)

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.make_filtering_bound_logger(levelno),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger: structlog.stdlib.BoundLogger = structlog.get_logger(logger_name)

    def bind(self, **kwargs: dict[str, object]) -> Logger:
        self.logger = self.logger.bind(**kwargs)

        return self

    def debug(self, *args: object, sep: str = " ", **kwargs: dict[str, object]) -> None:
        self.logger.log(logging.DEBUG, sep.join(map(str, args)), **kwargs)

    def info(self, *args: object, sep: str = " ", **kwargs: dict[str, object]) -> None:
        self.logger.log(logging.INFO, sep.join(map(str, args)), **kwargs)

    def warning(
        self, *args: object, sep: str = " ", **kwargs: dict[str, object]
    ) -> None:
        self.logger.log(logging.WARNING, sep.join(map(str, args)), **kwargs)

    def warn(self, *args: object, sep: str = " ", **kwargs: dict[str, object]) -> None:
        self.warning(*args, sep=sep, **kwargs)

    def error(self, *args: object, sep: str = " ", **kwargs: dict[str, object]) -> None:
        self.logger.log(logging.ERROR, sep.join(map(str, args)), **kwargs)

    def critical(
        self, *args: object, sep: str = " ", **kwargs: dict[str, object]
    ) -> None:
        self.logger.log(logging.CRITICAL, sep.join(map(str, args)), **kwargs)

    def fatal(self, *args: object, sep: str = " ", **kwargs: dict[str, object]) -> None:
        self.critical(*args, sep=sep, **kwargs)


if __name__ == "__main__":
    logger = Logger(log_file="richstructlog4.log")

    logger.info("Starting application")
    logger.debug("Debug information")
    logger.warning("Warning message")
    logger.error("Error occurred")
    logger.critical("Critical error!")

    logger.info("Here are rich text markup examples:")
    logger.debug(" - This is a debug message which most likely won't be seen")
    logger.info(" - We are hiring. Visit our [link=https://map4.jp]website[/link]!")
    logger.warning(" - :warning-emoji: We are going to have a problem")
    logger.error(" - [bold red]ALERT![/bold red] Something happened")
    logger.critical(" - :fire: :boom: :scream: :fire: :boom: :scream:")

    print()

    logger.info("The following texts are automatically highlighted:")
    logger.info(" - XML/HTML: `<tag>content</tag>`")
    logger.info(" - IP addresses: `192.168.1.1`, `2001:db8::1`")
    logger.info(" - MAC addresses: `00:1B:44:11:3A:B7`")
    logger.info(" - UUIDs: `123e4567-e89b-12d3-a456-426614174000`")
    logger.info(" - Python literals: `True`, `False`, `None`")
    logger.info(" - Numbers: `42`, `3.14`, `1+2j`")
    logger.info(" - Paths: `/usr/local/bin`")
    logger.info(" - URLs: `https://map4.jp`")
