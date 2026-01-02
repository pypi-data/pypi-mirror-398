from __future__ import annotations

import logging
import os
import shutil
import sys
import time
import unicodedata
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Literal, TypeVar

import psutil
from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


class ContextInjector(logging.Filter):
    """Inject context to logging.

    Logging injector base on `logging.Filter`, can inject context information like cpu
    usage, memory usage, time consumption, console width, etc.
    """

    def __init__(self) -> None:
        super().__init__(name="")
        self._context: dict[str, Any] = {}

    @staticmethod
    def ms2human(ms: float) -> str:
        if ms < 1000:
            return f"{ms:.2f}ms"
        elif ms < 1000 * 60:
            return f"{ms / 1000:.2f}s"
        elif ms < 1000 * 60 * 60:
            return f"{ms / 1000 / 60:.2f}m"
        else:
            return f"{ms / 1000 / 60 / 60:.2f}h"

    def get_duration(self) -> str:
        last_call = self._context.get("last_call")
        now = time.time()
        if isinstance(last_call, (float, int)) and now > last_call:
            duration = self.ms2human((now - last_call) * 1000)
        else:
            duration = self.ms2human(0)

        self._context["last_call"] = now
        return duration

    @staticmethod
    def get_psinfo() -> tuple[float, float]:
        mem_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        return mem_usage, cpu_usage

    def get_context(self, record: logging.LogRecord) -> dict[str, tuple[str, Any]]:
        try:
            _context = getattr(record, "_context")
            assert isinstance(_context, dict), "_context should be dict"
        except AttributeError:
            record._context = {}
            _context = getattr(record, "_context")

        return _context

    def filter(self, record: logging.LogRecord):
        _context = self.get_context(record)

        _context["duration"] = (" ⏱️ ", self.get_duration())

        mem_usage, cpu_usage = self.get_psinfo()
        _context["mem_usage"] = (" 🖥️ ", f"{mem_usage:.0f}%")
        _context["cpu_usage"] = (" 🤖 ", f"{cpu_usage:.0f}%")
        return True


class ContextFormatter(logging.Formatter):
    """Context formatter"""

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        context_left: list[str] | None = None,
        context_right: list[str] | None = None,
    ):
        super().__init__(fmt, datefmt, style, validate)
        self.context_left = context_left or []
        self.context_right = context_right or ["duration"]

    @staticmethod
    def get_whitespace(message: str) -> int:
        console_width = shutil.get_terminal_size().columns
        length = sum(2 if unicodedata.east_asian_width(c) in ("F", "W", "A") else 1 for c in message.split("\n")[-1])
        count = console_width - (length % console_width)
        return count

    def format(self, record: logging.LogRecord) -> str:
        """Format message with context infomation.

        Try to format context messasge with context information
        """

        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)

        # try to inject
        try:
            context: dict = getattr(record, "_context")

            context_left = ""
            for ct in self.context_left:
                if ct in context.keys():
                    context_left += f"{context[ct][0]} {context[ct][1]} "

            context_right = ""
            for ct in self.context_right:
                if ct in context.keys():
                    context_right += f"{context[ct][0]} {context[ct][1]} "

            whitespace = " " * self.get_whitespace(f"{context_left} {s} {context_right}")
            record.message = f"{context_left} {record.message} {whitespace} {context_right}"
            s = self.formatMessage(record)

        except Exception:
            pass

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        return s


def setup_logger(
    name: str,
    level: int = logging.INFO,
    fmt: str = "[{levelname:.04}] {asctime} {message} [{filename}:{lineno}]",
    datefmt="%m-%d %H:%M:%S",
    injector: ContextInjector | None = None,
    formatter: logging.Formatter | None = None,
) -> logging.Logger:
    """Setup logger by name and level.

    Setting up global unique logger with name and default level, the setup process
    will remove existed logger.

    Parameters
    ----------
    name : str
        Logger name.
    level : int
        defualt level of stream handler.

    Return
    ------
    logger : logging.Logger
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(1)

    if injector is None:
        injector = ContextInjector()

    if formatter is None:
        formatter = ContextFormatter(
            fmt=fmt,
            datefmt=datefmt,
            style="{",
            context_left=["mem_usage"],
            context_right=["duration"],
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    handler.addFilter(injector)

    logger.addHandler(handler)
    return logger


def add_file_logger(
    logger: logging.Logger | str,
    filepath: Path | str,
    level: int,
    injector: ContextInjector | None = None,
    formatter: logging.Formatter | None = None,
) -> logging.Logger:
    """Add logging file handler."""

    if isinstance(logger, str):
        logger = logging.getLogger(logger)
    elif isinstance(logger, logging.Logger):
        logger = logger
    else:
        raise TypeError(f"logger must be string or logging.Logger, got {type(logger)}")

    handler = logging.FileHandler(filepath, encoding="utf-8")
    if injector is not None:
        handler.addFilter(injector)
    if formatter is None:
        formatter = logging.Formatter(
            fmt="[{name}.{levelname:.04}] {asctime} {message}",
            datefmt="%m-%d %H:%M:%S",
            style="{",
        )
    handler.setFormatter(formatter)
    handler.setLevel(level)

    for hdlr in logger.handlers:
        if isinstance(hdlr, logging.FileHandler):
            if os.path.samefile(hdlr.baseFilename, handler.baseFilename):
                logger.removeHandler(hdlr)

    logger.addHandler(handler)
    return logger


def silent_on_error(func: Callable[P, R]) -> Callable[P, R | None]:
    """装饰器：方法报错时返回 None"""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            tb = exc.__traceback__
            while tb and tb.tb_next:
                tb = tb.tb_next
            if tb is not None:
                filename = tb.tb_frame.f_code.co_filename
                lineno = tb.tb_lineno
                funcname = tb.tb_frame.f_code.co_name
                logger.error(f"Calling {filename}:{lineno} - {funcname}(*) failed: {exc}")
            else:
                # 兜底
                logger.error(f"Calling {getattr(func, '__qualname__')}(*) failed: {exc}")
            return None

    return wrapper
