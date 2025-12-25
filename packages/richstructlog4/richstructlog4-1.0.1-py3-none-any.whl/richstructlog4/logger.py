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


class _RichConsoleHandler(logging.Handler):
    def __init__(self, console: Console) -> None:
        super().__init__()
        self.console = console

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return

        msg = msg.rstrip("\n")
        try:
            self.console.print(Text.from_ansi(msg), highlight=False)
        except Exception:
            self.handleError(record)


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

        if console is None:
            stdout_handler: logging.Handler = logging.StreamHandler(sys.stdout)
            stderr_handler: logging.Handler = logging.StreamHandler(sys.stderr)
        else:
            stdout_handler = _RichConsoleHandler(self.console)
            stderr_handler = _RichConsoleHandler(self.console)

        stdout_handler.addFilter(_LessThanLevelFilter(logging.WARNING))
        stdout_handler.setLevel(levelno)
        stdout_handler.setFormatter(console_formatter)

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

    def bind(self, **kwargs: object) -> Logger:
        self.logger = self.logger.bind(**kwargs)

        return self

    def debug(self, *args: object, sep: str = " ", **kwargs: object) -> None:
        self.logger.log(logging.DEBUG, sep.join(map(str, args)), **kwargs)

    def info(self, *args: object, sep: str = " ", **kwargs: object) -> None:
        self.logger.log(logging.INFO, sep.join(map(str, args)), **kwargs)

    def warning(
        self, *args: object, sep: str = " ", **kwargs: object
    ) -> None:
        self.logger.log(logging.WARNING, sep.join(map(str, args)), **kwargs)

    def warn(self, *args: object, sep: str = " ", **kwargs: object) -> None:
        self.warning(*args, sep=sep, **kwargs)

    def error(self, *args: object, sep: str = " ", **kwargs: object) -> None:
        self.logger.log(logging.ERROR, sep.join(map(str, args)), **kwargs)

    def critical(
        self, *args: object, sep: str = " ", **kwargs: object
    ) -> None:
        self.logger.log(logging.CRITICAL, sep.join(map(str, args)), **kwargs)

    def fatal(self, *args: object, sep: str = " ", **kwargs: object) -> None:
        self.critical(*args, sep=sep, **kwargs)


if __name__ == "__main__":
    import os
    import time

    # Rich imports
    from rich import box
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.pretty import Pretty
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TransferSpeedColumn,
    )
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    # === Configuration ===
    # Set this environment variable to "1" to skip delays for testing
    demo_fast = os.environ.get("RICHSTRUCTLOG4_DEMO_FAST") == "1"

    # Increase steps for a longer, more dramatic effect
    total_steps = 10 if demo_fast else 200
    base_sleep = 0.0 if demo_fast else 0.04

    console = Console()

    logger = Logger(log_file="demo.log", console=console)

    # === Narrative Helper Functions ===
    def type_writer(text, speed=0.03, style="bold green"):
        """Simulates typing text on a terminal."""
        console.print("> [bold cyan]AI-CORE:[/]", end=" ")
        for char in text:
            console.print(char, style=style, end="")
            if not demo_fast:
                time.sleep(speed)
        console.print("") # Newline
        if not demo_fast:
            time.sleep(0.5)

    def cinematic_pause(duration=1.0):
        if not demo_fast:
            time.sleep(duration)

    # ==========================================
    # ACT 1: THE AWAKENING
    # ==========================================
    console.clear()

    # Boot Sequence Panel
    console.print(
        Panel(
            "[bold cyan]SYSTEM BOOT SEQUENCE v9.2[/]\n[dim]Loading Core Modules...[/]",
            box=box.DOUBLE_EDGE,
            title="TERMINAL ACCESS",
            subtitle="Secure Connection",
            style="cyan"
        )
    )
    cinematic_pause(1)

    logger.info("Initializing main kernel...")
    cinematic_pause(0.5)
    logger.debug("Mounting file system: /dev/sda1 -> /root", mount_point="/root", fs_type="ext4")
    logger.debug("Checking memory integrity...", available_ram="64GB", status="OK")
    logger.info("Neural Interface established.", latency="2ms")

    type_writer("Greetings, Commander. All systems are nominal.")
    type_writer("Scanning deep space frequencies for incoming data...")

    # ==========================================
    # ACT 2: THE INTERCEPTION (Table Demo)
    # ==========================================
    cinematic_pause(1)
    logger.warning("Anomalous signal detected in Sector 7G.")

    console.print(Panel("[blink bold red]⚠ WARNING: UNKNOWN ENCRYPTION DETECTED[/]", style="red", box=box.HEAVY))
    cinematic_pause(1)

    type_writer("Visualizing intercepted packet headers. Analyzing structure...")

    # Creating a rich Table
    table = Table(title="Intercepted Signal Manifest", box=box.ROUNDED, show_lines=True)
    table.add_column("Packet ID", style="cyan", no_wrap=True)
    table.add_column("Origin", style="magenta")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Protocol", justify="center")
    table.add_column("Threat Level", style="red")

    # Add rows with a slight delay to simulate loading
    signals = [
        ("SIG-Alpha", "Proxima Centauri", "42 TB", "TCP/IP (Legacy)", "Low"),
        ("SIG-Beta",  "Unknown Nebula",   "12 PB", "Quantum-Ent.",  "High"),
        ("SIG-Gamma", "Voyager 2",        "12 KB", "Analog",        "None"),
        ("SIG-Delta", "Dark Sector",      "?? PB", "[bold red]Alien[/]", "[blink]CRITICAL[/]"),
    ]

    with Live(table, console=console, refresh_per_second=12, transient=False) as live:
        for row in signals:
            table.add_row(*row)
            live.update(table)
            cinematic_pause(0.3)
    logger.critical("Packet SIG-Delta contains a self-replicating polymorphic code.")

    # ==========================================
    # ACT 3: DEEP DIVE (Pretty Print Demo)
    # ==========================================
    cinematic_pause(1)
    type_writer("Isolating the virus structure. Dumping hex object to console...")

    # Complex nested dictionary for Pretty print
    alien_virus_data = {
        "entity_id": "XENOMORPH_CODE_V4",
        "origin": {"coordinates": [45.22, -12.01, 88.99], "galaxy": "Andromeda"},
        "behavior": {
            "replication_rate": float("inf"),
            "target_modules": ["Oxygen", "Gravity", "CoffeeMachine"],
            "is_sentient": True
        },
        "payload_signature": bytes.fromhex("DEADBEEF CAFEBABE 0000FFFF"),
        " countermeasures_active": False
    }

    console.print(Pretty(alien_virus_data, expand_all=True))
    logger.error("Automatic containment failed. Manual override required.")

    # ==========================================
    # ACT 4: THE FIX (Syntax Highlighting Demo)
    # ==========================================
    cinematic_pause(1)
    type_writer("Commander, I have generated a counter-measure script. Reviewing syntax...")

    # Python code snippet
    counter_measure_code = """
import time
from defense_grid import Firewall, Exorcism

def deploy_counter_measure(target_id):
    \"\"\"
    Purges the alien code from the mainframe.
    WARNING: May cause temporal displacement.
    \"\"\"
    system = Firewall()
    try:
        print(f"Locking onto {target_id}...")
        system.isolate_sector("SECTOR_7G")

        # Deploy quantum decryption
        for attempt in range(100):
            key = system.generate_quantum_key()
            if system.unlock(target_id, key):
                return True

    except SystemOverload as e:
        # Emergency coolant flush
        system.flush_coolant(level="MAX")
        raise e

    return False
    """

    console.print(
        Syntax(
            counter_measure_code,
            "python",
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
    )

    type_writer("Script validated. Executing counter-measure protocols now.")

    # ==========================================
    # ACT 5: THE BATTLE (Progress Bar Demo)
    # ==========================================

    # Setup Progress Bars
    progress = Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        "•",
        TimeElapsedColumn(),
        "•",
        TransferSpeedColumn(),
        console=console,
        transient=False
    )

    task_compile = progress.add_task("Compiling Exploit...", total=total_steps)
    task_upload  = progress.add_task("Uploading Payload...", total=total_steps, visible=False)
    task_purge   = progress.add_task("Purging System...", total=total_steps, visible=False)

    with progress:
        # Phase 1: Compile
        for i in range(total_steps):
            progress.update(task_compile, advance=1)

            # Log events during progress
            if i == int(total_steps * 0.2):
                logger.debug("Compiling libraries: numpy, pandas, astro-physics-lib")
            if i == int(total_steps * 0.8):
                logger.info("Compilation successful. Binaries ready.")

            time.sleep(base_sleep / 2)

        # Phase 2: Upload
        progress.update(task_upload, visible=True)
        for i in range(total_steps):
            progress.update(task_upload, advance=1)

            if i == int(total_steps * 0.3):
                logger.warning("Bandwidth fluctuating. Rerouting via satellite.")
            if i == int(total_steps * 0.6):
                logger.debug("Bypassing alien firewall...")

            time.sleep(base_sleep)

        # Phase 3: Purge (The intense part)
        progress.update(task_purge, visible=True)
        for i in range(total_steps):
            progress.update(task_purge, advance=1)

            if i == int(total_steps * 0.1):
                logger.info("Purge sequence initiated.")
            if i == int(total_steps * 0.5):
                logger.critical("CPU Temperature critical! (98°C)")
                progress.console.print("[bold red blink]>> COOLANT FLUSH TRIGGERED <<[/]")
            if i == int(total_steps * 0.9):
                logger.info("Threat eliminated. System stabilizing.")

            time.sleep(base_sleep * 1.5)

    # ==========================================
    # ACT 6: VICTORY & CAPABILITIES (Highlight Demo)
    # ==========================================
    console.clear()
    console.print(Panel("[bold green]MISSION ACCOMPLISHED[/]", style="white on green", box=box.HEAVY))
    cinematic_pause(1)

    type_writer("System upgraded. Enhanced logging capabilities are now active.")
    type_writer("Scanning logs for auto-highlighting patterns...")

    console.print(Panel("RichStructLog4: Auto-Highlighting Demo", style="magenta"))

    # Demonstrating regex/pattern highlighting
    examples = [
        "Connection from IP `192.168.1.55` established on port `8080`.",
        "User UUID `550e8400-e29b-41d4-a716-446655440000` authenticated.",
        "MAC Address `00:1A:2B:3C:4D:5E` added to whitelist.",
        "Python boolean logic: `True` is not `False`, and `None` is void.",
        "Complex numbers detected: `3.14159` + `2j`.",
        "Log file path: `/var/log/richstructlog4/system.log`",
        "Documentation available at `https://github.com/Textualize/rich`",
        "Email alert sent to `admin@starfleet.com`"
    ]

    for msg in examples:
        logger.info(f"Log Entry: {msg}")
        time.sleep(base_sleep * 2)

    console.print()
    logger.info("Rich Text Support:")
    logger.info(" - We can use [bold red]Bold Red[/] for emphasis.")
    logger.info(" - We support emoji! :rocket: :alien: :computer:")
    logger.info(" - Even [link=https://www.google.com]clickable links[/link] in supported terminals.")

    cinematic_pause(1)

    console.print(
        Panel(
            "[bold white]Simulation Complete.[/]\n[italic cyan]\"Logs are the memory of the machine.\"[/]",
            box=box.DOUBLE,
            style="blue"
        )
    )
