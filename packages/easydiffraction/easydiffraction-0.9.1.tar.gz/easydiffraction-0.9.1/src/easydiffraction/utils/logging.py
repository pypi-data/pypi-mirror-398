# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Project-wide logging utilities built on top of Rich.

Provides a shared Rich console, a compact/verbose logger with consistent
formatting, Jupyter traceback handling, and a small printing façade
tailored to the configured console.
"""

from __future__ import annotations

import logging
import os
import shutil
import warnings
from contextlib import suppress
from enum import Enum
from enum import IntEnum
from enum import auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

import re
import sys
from pathlib import Path

from rich import traceback
from rich.console import Console
from rich.console import Group
from rich.console import RenderableType
from rich.logging import RichHandler
from rich.text import Text

from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.environment import in_pytest
from easydiffraction.utils.environment import in_warp

# ======================================================================
# HANDLERS
# ======================================================================


class IconifiedRichHandler(RichHandler):
    """RichHandler that uses icons for log levels in compact mode, Rich
    default in verbose mode.
    """

    _icons = {
        logging.CRITICAL: '💀',
        logging.ERROR: '❌',
        logging.WARNING: '⚠️',
        logging.DEBUG: '⚙️',
        logging.INFO: 'ℹ️',
    }

    def __init__(self, *args, mode: str = 'compact', **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def get_level_text(self, record: logging.LogRecord) -> Text:
        if self.mode == 'compact':
            icon = self._icons.get(record.levelno, record.levelname)
            if in_warp() and not in_jupyter() and icon in ['⚠️', '⚙️', 'ℹ️']:
                icon = icon + ' '  # add space to align with two-char icons
            return Text(icon)
        else:
            # Use RichHandler's default level text for verbose mode
            return super().get_level_text(record)

    def render_message(self, record: logging.LogRecord, message: str) -> Text:
        # In compact mode, let the icon come from get_level_text and
        # keep the message body unadorned. In verbose mode, defer to
        # RichHandler.
        if self.mode == 'compact':
            try:
                return Text.from_markup(message)
            except Exception:
                return Text(str(message))
        return super().render_message(record, message)


# ======================================================================
# CONSOLE MANAGER
# ======================================================================


class ConsoleManager:
    """Central provider for shared Rich Console instance."""

    _MIN_CONSOLE_WIDTH = 130
    _instance: Console | None = None

    @staticmethod
    def _detect_width() -> int:
        """Detect a suitable console width for the shared Console.

        Returns:
            The detected terminal width, clamped at
            ``_MIN_CONSOLE_WIDTH`` to avoid cramped layouts.
        """
        min_width = ConsoleManager._MIN_CONSOLE_WIDTH
        try:
            width = shutil.get_terminal_size().columns
        except Exception:
            width = min_width
        return max(width, min_width)

    @classmethod
    def get(cls) -> Console:
        """Return a shared Rich Console instance."""
        if cls._instance is None:
            cls._instance = Console(
                width=cls._detect_width(),
                force_jupyter=False,
            )
        return cls._instance


# ======================================================================
# LOGGER CONFIGURATION HELPERS
# ======================================================================


class LoggerConfig:
    """Facade for logger configuration, delegates to helpers."""

    @staticmethod
    def setup_handlers(
        logger: logging.Logger,
        *,
        level: int,
        rich_tracebacks: bool,
        mode: str = 'compact',
    ) -> None:
        """Install Rich handler and optional Jupyter traceback support.

        Args:
            logger: Logger instance to attach handlers to.
            level: Minimum log level to emit.
            rich_tracebacks: Whether to enable Rich tracebacks.
            mode: Output mode name ("compact" or "verbose").
        """
        logger.handlers.clear()
        logger.propagate = False
        logger.setLevel(level)

        if in_jupyter():
            traceback.install(
                show_locals=False,
                suppress=['easydiffraction'],
            )

        console = ConsoleManager.get()
        handler = IconifiedRichHandler(
            rich_tracebacks=rich_tracebacks,
            markup=True,
            show_time=False,
            show_path=False,
            tracebacks_show_locals=False,
            tracebacks_suppress=['easydiffraction'],
            tracebacks_max_frames=10,
            console=console,
            mode=mode,
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

    @staticmethod
    def configure(
        logger: logging.Logger,
        *,
        mode: 'Logger.Mode',
        level: 'Logger.Level',
        rich_tracebacks: bool,
    ) -> None:
        """Configure the logger with RichHandler and exception hooks.

        Args:
            logger: Logger instance to configure.
            mode: Output mode (compact or verbose).
            level: Minimum log level to emit.
            rich_tracebacks: Whether to enable Rich tracebacks.
        """
        LoggerConfig.setup_handlers(
            logger,
            level=int(level),
            rich_tracebacks=rich_tracebacks,
            mode=mode.value,
        )

        if rich_tracebacks and mode == Logger.Mode.VERBOSE:
            ExceptionHookManager.install_verbose_hook(logger)
        elif mode == Logger.Mode.COMPACT:
            ExceptionHookManager.install_compact_hook(logger)
            ExceptionHookManager.install_jupyter_traceback_suppressor(logger)
        else:
            ExceptionHookManager.restore_original_hook()


class ExceptionHookManager:
    """Handles installation and restoration of exception hooks."""

    @staticmethod
    def install_verbose_hook(logger: logging.Logger) -> None:
        """Install a verbose exception hook that prints rich tracebacks.

        Args:
            logger: Logger used to emit the exception information.
        """
        if not hasattr(Logger, '_orig_excepthook'):
            Logger._orig_excepthook = sys.excepthook  # type: ignore[attr-defined]

        def aligned_excepthook(
            exc_type: type[BaseException],
            exc: BaseException,
            tb: 'TracebackType | None',
        ) -> None:
            original_args = getattr(exc, 'args', tuple())
            message = str(exc)
            with suppress(Exception):
                exc.args = tuple()
            try:
                logger.error(message, exc_info=(exc_type, exc, tb))
            except Exception:
                logger.error('Unhandled exception (logging failure)')
            finally:
                with suppress(Exception):
                    exc.args = original_args

        sys.excepthook = aligned_excepthook  # type: ignore[assignment]

    @staticmethod
    def install_compact_hook(logger: logging.Logger) -> None:
        """Install a compact exception hook that logs message-only.

        Args:
            logger: Logger used to emit the error message.
        """
        if not hasattr(Logger, '_orig_excepthook'):
            Logger._orig_excepthook = sys.excepthook  # type: ignore[attr-defined]

        def compact_excepthook(
            _exc_type: type[BaseException],
            exc: BaseException,
            _tb: 'TracebackType | None',
        ) -> None:
            logger.error(str(exc))
            raise SystemExit(1)

        sys.excepthook = compact_excepthook  # type: ignore[assignment]

    @staticmethod
    def restore_original_hook():
        """Restore the original sys.excepthook if it was overridden."""
        if hasattr(Logger, '_orig_excepthook'):
            sys.excepthook = Logger._orig_excepthook  # type: ignore[attr-defined]

    # Jupyter-specific traceback suppression (inlined here)
    @staticmethod
    def _suppress_traceback(logger):
        """Build a Jupyter custom exception callback that logs only the
        message.

        Args:
            logger: Logger used to emit error messages.

        Returns:
            A callable suitable for IPython's set_custom_exc that
            suppresses full tracebacks and logs only the exception
            message.
        """

        def suppress_jupyter_traceback(*args, **kwargs):
            try:
                _evalue = (
                    args[2] if len(args) > 2 else kwargs.get('_evalue') or kwargs.get('evalue')
                )
                logger.error(str(_evalue))
            except Exception as err:
                logger.debug('Jupyter traceback suppressor failed: %r', err)
            return None

        return suppress_jupyter_traceback

    @staticmethod
    def install_jupyter_traceback_suppressor(logger: logging.Logger) -> None:
        """Install a Jupyter/IPython custom exception handler that
        suppresses tracebacks.

        Args:
            logger: Logger used to emit error messages.
        """
        try:
            from IPython import get_ipython

            ip = get_ipython()
            if ip is not None:
                ip.set_custom_exc(
                    (BaseException,), ExceptionHookManager._suppress_traceback(logger)
                )
        except Exception as err:
            msg = f'Failed to install Jupyter traceback suppressor: {err!r}'
            logger.debug(msg)


# ======================================================================
# LOGGER CORE
# ======================================================================


class Logger:
    """Centralized logging with Rich formatting and two modes.

    Environment variables:
    ED_LOG_MODE: set default mode ('verbose' or 'compact')
    ED_LOG_LEVEL: set default level ('DEBUG', 'INFO', etc.)
    """

    # --- Enums ---
    class Mode(Enum):
        """Output modes (see :class:`Logger`)."""

        VERBOSE = 'verbose'  # rich traceback panel
        COMPACT = 'compact'  # single line; no traceback

        @classmethod
        def default(cls):
            return cls.COMPACT

    class Level(IntEnum):
        """Mirror stdlib logging levels."""

        DEBUG = logging.DEBUG
        INFO = logging.INFO
        WARNING = logging.WARNING
        ERROR = logging.ERROR
        CRITICAL = logging.CRITICAL

        @classmethod
        def default(cls):
            return cls.WARNING

    class Reaction(Enum):
        """Reaction to errors (see :class:`Logger`)."""

        RAISE = auto()
        WARN = auto()

        @classmethod
        def default(cls):
            return cls.RAISE

    # --- Internal state ---
    _logger = logging.getLogger('easydiffraction')
    _configured = False
    _mode: Mode = Mode.VERBOSE
    _reaction: Reaction = Reaction.RAISE  # TODO: not default?
    _console = ConsoleManager.get()

    # ===== CONFIGURATION =====
    @classmethod
    def configure(
        cls,
        *,
        mode: Mode | None = None,
        level: Level | None = None,
        reaction: Reaction | None = None,
        rich_tracebacks: bool | None = None,
    ) -> None:
        """Configure logger.

        mode: default COMPACT in Jupyter else VERBOSE
        level: minimum log level
        rich_tracebacks: override automatic choice

        Environment variables:
        ED_LOG_MODE: set default mode ('verbose' or 'compact')
        ED_LOG_LEVEL: set default level ('DEBUG', 'INFO', etc.)
        """
        env_mode = os.getenv('ED_LOG_MODE')
        env_level = os.getenv('ED_LOG_LEVEL')
        env_reaction = os.getenv('ED_LOG_REACTION')

        # Read from environment if not provided
        if mode is None and env_mode is not None:
            with suppress(ValueError):
                mode = Logger.Mode(env_mode.lower())
        if level is None and env_level is not None:
            with suppress(KeyError):
                level = Logger.Level[env_level.upper()]
        if reaction is None and env_reaction is not None:
            with suppress(KeyError):
                reaction = Logger.Reaction[env_reaction.upper()]

        # Set defaults if still None
        if mode is None:
            mode = Logger.Mode.default()
        if level is None:
            level = Logger.Level.default()
        if reaction is None:
            reaction = Logger.Reaction.default()

        cls._mode = mode
        cls._reaction = reaction

        if rich_tracebacks is None:
            rich_tracebacks = mode == Logger.Mode.VERBOSE

        LoggerConfig.configure(
            logger=cls._logger,
            mode=mode,
            level=level,
            rich_tracebacks=rich_tracebacks,
        )
        cls._configured = True

    @classmethod
    def _install_jupyter_traceback_suppressor(cls) -> None:
        """Install traceback suppressor in Jupyter, safely and lint-
        clean.
        """
        ExceptionHookManager.install_jupyter_traceback_suppressor(cls._logger)

    # ===== Helpers =====
    @classmethod
    def set_mode(cls, mode: Mode) -> None:
        cls.configure(mode=mode, level=cls.Level(cls._logger.level))

    @classmethod
    def set_level(cls, level: Level) -> None:
        cls.configure(mode=cls._mode, level=level)

    @classmethod
    def mode(cls) -> Mode:
        return cls._mode

    @classmethod
    def _lazy_config(cls) -> None:
        if not cls._configured:  # pragma: no cover - trivial
            cls.configure()

    # ===== Core Routing =====
    @classmethod
    def handle(
        cls,
        *messages: str,
        level: Level = Level.ERROR,
        exc_type: type[BaseException] | None = AttributeError,
    ) -> None:
        """Route a log message (see class docs for policy)."""
        cls._lazy_config()
        message = ' '.join(messages)
        # Prioritize explicit UserWarning path so pytest captures
        # warnings
        if exc_type is UserWarning:
            if in_pytest():
                warnings.warn(message, UserWarning, stacklevel=2)
            else:
                cls._logger.warning(message)
            return
        # Special handling for Reaction.WARN (non-warning cases)
        if cls._reaction is cls.Reaction.WARN:
            # Log as error/critical (keep icon) but continue execution
            cls._logger.log(int(level), message)
            return
        if exc_type is not None:
            if cls._mode is cls.Mode.VERBOSE:
                raise exc_type(message)
            if cls._mode is cls.Mode.COMPACT:
                raise exc_type(message) from None
        cls._logger.log(int(level), message)

    # ==================================================================
    # CONVENIENCE API
    # ==================================================================

    @classmethod
    def debug(cls, *messages: str) -> None:
        cls.handle(*messages, level=cls.Level.DEBUG, exc_type=None)

    @classmethod
    def info(cls, *messages: str) -> None:
        cls.handle(*messages, level=cls.Level.INFO, exc_type=None)

    @classmethod
    def warning(cls, *messages: str, exc_type: type[BaseException] | None = None) -> None:
        cls.handle(*messages, level=cls.Level.WARNING, exc_type=exc_type)

    @classmethod
    def error(cls, *messages: str, exc_type: type[BaseException] = AttributeError) -> None:
        cls.handle(*messages, level=cls.Level.ERROR, exc_type=exc_type)

    @classmethod
    def critical(cls, *messages: str, exc_type: type[BaseException] = RuntimeError) -> None:
        cls.handle(*messages, level=cls.Level.CRITICAL, exc_type=exc_type)


# ======================================================================
# PRINTER
# ======================================================================


class ConsolePrinter:
    """Printer utility that prints objects to the shared console with
    left padding.
    """

    _console = ConsoleManager.get()

    @classmethod
    def print(cls, *objects, **kwargs):
        """Print objects to the console with left padding.

        - Renderables (Rich types like Text, Table, Panel, etc.) are
          kept as-is.
        - Non-renderables (ints, floats, Path, etc.) are converted to
          str().
        """
        safe_objects = []
        for obj in objects:
            if isinstance(obj, RenderableType):
                safe_objects.append(obj)
            elif isinstance(obj, Path):
                safe_objects.append(str(obj))
            else:
                safe_objects.append(str(obj))

        # If multiple objects, join with spaces
        renderable = (
            ' '.join(str(o) for o in safe_objects)
            if all(isinstance(o, str) for o in safe_objects)
            else Group(*safe_objects)
        )

        cls._console.print(renderable, **kwargs)

    @classmethod
    def paragraph(cls, title: str) -> None:
        parts = re.split(r"('.*?')", title)
        text = Text()
        for part in parts:
            if part.startswith("'") and part.endswith("'"):
                text.append(part)
            else:
                text.append(part, style='bold blue')
        formatted = f'{text.markup}'
        if not in_jupyter():
            formatted = f'\n{formatted}'
        cls._console.print(formatted)

    @classmethod
    def section(cls, title: str) -> None:
        """Formats a section header with bold green text."""
        full_title = f'{title.upper()}'
        line = '━' * len(full_title)
        formatted = f'[bold green]\n{line}\n{full_title}\n{line}[/bold green]'
        if not in_jupyter():
            formatted = f'\n{formatted}'
        cls._console.print(formatted)

    @classmethod
    def chapter(cls, title: str) -> None:
        """Formats a chapter header with bold magenta text, uppercase,
        and padding.
        """
        width = ConsoleManager._detect_width()
        symbol = '─'
        full_title = f' {title.upper()} '
        pad_len = (width - len(full_title)) // 2
        padding = symbol * pad_len
        line = f'[bold magenta]{padding}{full_title}{padding}[/bold magenta]'
        if len(line) < width:
            line += symbol
        formatted = f'{line}'
        if not in_jupyter():
            formatted = f'\n{formatted}'
        cls._console.print(formatted)


# Configure logging at import time
Logger.configure()

# Convenient alias for logger
log = Logger

# Convenient alias for console printer
console = ConsolePrinter
