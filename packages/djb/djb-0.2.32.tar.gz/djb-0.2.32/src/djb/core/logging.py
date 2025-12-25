"""
djb logging - Consistent progress output with verbosity control.

Provides a structured logging system with different log levels and consistent
formatting. Used instead of click.echo and click.secho.

Log Level Design
----------------
The log levels are designed for CLI output, not traditional logging:

- ERROR: Something failed, operation cannot continue (✗ prefix)
- WARNING: Something unexpected but operation continues (! prefix)
- INFO: Standard output, no prefix
- NOTE: Important information that should be visible by default
- DEBUG: Detailed output for troubleshooting (indented)

The CliLogger class provides semantic methods that provide consistent
formatting:

- done(): Step completed successfully (✓ prefix)
- next(): Starting a new step (adds ... suffix)
- skip(): Step skipped (>> prefix)
- tip(): Helpful suggestions (Tip: prefix)
- obs(): Observations about system state (* prefix)
- fail(): A check/validation failed (✗ prefix)

Why FlushingStreamHandler?
--------------------------
Heroku dynos and similar environments buffer stdout. Without explicit
flushing, users see no output until the buffer fills or the process exits.
This makes long-running commands appear frozen. The FlushingStreamHandler
flushes after every log message to ensure immediate visibility.

Usage:
    from djb.core.logging import get_logger, setup_logging

    setup_logging("info")  # Call once at CLI entry
    logger = get_logger(__name__)

    logger.next("Installing dependencies")  # Installing dependencies...
    logger.done("Installed 42 packages")    # ✓ Installed 42 packages
    logger.tip("Run 'djb --help' for more") # Tip: Run 'djb --help' for more
"""

from __future__ import annotations

import logging
import sys
from enum import IntEnum

# Custom log level between INFO (20) and WARNING (30) for important but non-critical messages.
NOTE_LEVEL = logging.INFO + 5


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"


class Level(IntEnum):
    """Custom log levels with prefixes for CLI output.

    These levels control what gets displayed based on --log-level.
    The actual prefixes are applied by CliLogger methods, not by level.
    """

    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    NOTE = NOTE_LEVEL
    DEBUG = logging.DEBUG

    @classmethod
    def from_string(cls, level_str: str) -> int:
        """Convert string to log level.

        Args:
            level_str: One of 'error', 'warning', 'info', 'note', 'debug'

        Returns:
            The corresponding log level integer. Defaults to NOTE if unknown.
        """
        level_map = {
            "error": cls.ERROR,
            "warning": cls.WARNING,
            "info": cls.INFO,
            "note": cls.NOTE,
            "debug": cls.DEBUG,
        }
        return level_map.get(level_str.lower(), cls.NOTE)


class DjbFormatter(logging.Formatter):
    """Custom formatter that adds prefixes based on log level.

    All prefixes used in the CLI are defined here as a single source of truth.
    Colors: success in green, errors in red, warnings in yellow/orange.
    """

    # Prefixes for log levels (applied automatically by the formatter)
    # Colors without symbols - the color itself indicates the status
    PREFIXES = {
        logging.ERROR: f"{Colors.RED}",
        logging.WARNING: f"{Colors.YELLOW}",
        logging.INFO: "",
        NOTE_LEVEL: "",
        logging.DEBUG: "  ",
    }

    # Suffixes to reset colors after the message
    SUFFIXES = {
        logging.ERROR: Colors.RESET,
        logging.WARNING: Colors.RESET,
        logging.INFO: "",
        NOTE_LEVEL: "",
        logging.DEBUG: "",
    }

    # Prefixes for semantic methods (used by CliLogger)
    # Colors without symbols - the color itself indicates the status
    DONE = f"{Colors.GREEN}"
    DONE_SUFFIX = Colors.RESET
    FAIL = f"{Colors.RED}"
    FAIL_SUFFIX = Colors.RESET
    SKIP = ">> "
    TIP = f"{Colors.YELLOW}"
    TIP_SUFFIX = Colors.RESET
    NOTE = f"{Colors.CYAN}"
    NOTE_SUFFIX = Colors.RESET
    OBS = "* "
    NEXT_SUFFIX = "..."

    # Colors for highlighted/special text
    HIGHLIGHT = f"{Colors.CYAN}{Colors.BOLD}"
    HIGHLIGHT_SUFFIX = Colors.RESET

    # Section formatting
    SECTION = f"{Colors.CYAN}"
    SECTION_SUFFIX = Colors.RESET
    SECTION_WIDTH = 60

    def format(self, record):
        prefix = self.PREFIXES.get(record.levelno, "")
        suffix = self.SUFFIXES.get(record.levelno, "")
        # Store original message
        original_msg = record.msg
        # Add prefix and suffix to message
        record.msg = f"{prefix}{original_msg}{suffix}"
        # Format the record
        result = super().format(record)
        # Restore original message
        record.msg = original_msg
        return result


class FlushingStreamHandler(logging.StreamHandler):
    """Stream handler that flushes after each emit and uses current sys.stdout.

    This ensures output is visible immediately, which is important
    when running in environments like Heroku dynos where output
    might be buffered.

    The handler always uses the current sys.stdout at emit time (not at
    construction time), which is important for test compatibility with
    Click's CliRunner which temporarily replaces sys.stdout.
    """

    def __init__(self):
        # Don't pass a stream to parent - we'll provide it dynamically
        super().__init__(stream=None)

    @property
    def stream(self):
        """Always return the current sys.stdout."""
        return sys.stdout

    @stream.setter
    def stream(self, _value):
        """Ignore attempts to set stream - we always use sys.stdout."""
        pass

    def emit(self, record):
        super().emit(record)
        self.flush()


class DjbLogger:
    """Djb logger with semantic methods for different types of output.

    Rather than using traditional log levels, this logger provides methods
    for common CLI output patterns. Each method applies the appropriate
    prefix and uses the correct log level.

    The design follows the original djb codebase pattern of using semantic
    log methods (done, next, tip, obs) rather than relying solely on levels.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(f"djb.cli.{name}")

    def error(self, msg: str):
        """Log an error message (red).

        Use for errors that prevent operation from continuing.
        """
        self.logger.error(msg)

    def fail(self, msg: str):
        """Log a failure message (red).

        Use for check/validation failures that are expected conditions,
        as opposed to error() which is for unexpected problems.
        """
        self.logger.info(f"{DjbFormatter.FAIL}{msg}{DjbFormatter.FAIL_SUFFIX}")

    def warning(self, msg: str):
        """Log a warning message (yellow).

        Use for unexpected conditions that don't prevent operation.
        """
        self.logger.warning(msg)

    def info(self, msg: str):
        """Log an info message (no prefix).

        Use for general output that should always be visible.
        """
        self.logger.info(msg)

    def note(self, msg: str = ""):
        """Log a note (no prefix, NOTE level).

        Use for information that's useful but not essential.
        Visible at default log level.
        """
        self.logger.log(NOTE_LEVEL, msg)

    def debug(self, msg: str):
        """Log a debug message (indented).

        Use for detailed information useful during troubleshooting.
        Only visible when --log-level debug is set.
        """
        self.logger.debug(msg)

    def next(self, msg: str):
        """Log a next step message (adds '...' suffix).

        Use when starting a new operation step.
        Example: logger.next("Installing dependencies")
        Output:  Installing dependencies...
        """
        if not msg.endswith(DjbFormatter.NEXT_SUFFIX):
            msg = f"{msg}{DjbFormatter.NEXT_SUFFIX}"
        self.logger.info(msg)

    def done(self, msg: str):
        """Log a completion message (green).

        Use when an operation step completes successfully.
        Example: logger.done("Installed 42 packages")
        Output:  Installed 42 packages (in green)
        """
        self.logger.info(f"{DjbFormatter.DONE}{msg}{DjbFormatter.DONE_SUFFIX}")

    def skip(self, msg: str):
        """Log a skip message (>> prefix).

        Use when an operation step is skipped.
        Example: logger.skip("Frontend build (already up to date)")
        Output:  >> Frontend build (already up to date)
        """
        self.logger.info(f"{DjbFormatter.SKIP}{msg}")

    def tip(self, msg: str):
        """Log a tip message (yellow).

        Use for helpful suggestions that the user might not know.
        Example: logger.tip("Run 'djb --help' for more options")
        Output:  Run 'djb --help' for more options (in yellow)
        """
        self.logger.info(f"{DjbFormatter.TIP}{msg}{DjbFormatter.TIP_SUFFIX}")

    def obs(self, msg: str):
        """Log an observation message (* prefix).

        Use for observations about the system state.
        Example: logger.obs("Found 3 secrets files")
        Output:  * Found 3 secrets files
        """
        self.logger.info(f"{DjbFormatter.OBS}{msg}")

    def highlight(self, msg: str):
        """Log a highlighted message (cyan, bold).

        Use for important information that should stand out,
        like public keys or important values.
        Example: logger.highlight("age1abc...")
        """
        self.logger.info(f"{DjbFormatter.HIGHLIGHT}{msg}{DjbFormatter.HIGHLIGHT_SUFFIX}")

    def notice(self, msg: str):
        """Log a notice message (cyan).

        Use for informational notes to the user.
        Example: logger.notice("Running from djb directory, skipping host project checks.")
        Output:  Running from djb directory, skipping host project checks. (in cyan)
        """
        self.logger.info(f"{DjbFormatter.NOTE}{msg}{DjbFormatter.NOTE_SUFFIX}")

    def section(self, title: str):
        """Log a section header (cyan, with separator lines).

        Use for visual separation between major sections of output.
        Example: logger.section("Running health checks for djb")
        Output:
        ============================================================
        Running health checks for djb
        ============================================================
        """
        sep = "=" * DjbFormatter.SECTION_WIDTH
        self.logger.info("")
        self.logger.info(f"{DjbFormatter.SECTION}{sep}{DjbFormatter.SECTION_SUFFIX}")
        self.logger.info(f"{DjbFormatter.SECTION}{title}{DjbFormatter.SECTION_SUFFIX}")
        self.logger.info(f"{DjbFormatter.SECTION}{sep}{DjbFormatter.SECTION_SUFFIX}")
        self.logger.info("")


def setup_logging(level: str = "info"):
    """
    Set up logging for djb CLI commands.

    Args:
        level: Log level string (error, warning, info, note, debug)
    """
    log_level = Level.from_string(level)

    # Add NOTE level to logging module
    logging.addLevelName(NOTE_LEVEL, "NOTE")

    # Create handler with custom formatter
    # Use FlushingStreamHandler to ensure output is visible immediately
    # (important for Heroku dynos and other buffered environments)
    # The handler dynamically uses sys.stdout, making it compatible with CliRunner
    handler = FlushingStreamHandler()
    handler.setFormatter(DjbFormatter("%(message)s"))
    handler.setLevel(logging.DEBUG)  # Handler should process all levels

    # Configure root djb.cli logger
    cli_logger = logging.getLogger("djb.cli")
    cli_logger.setLevel(log_level)
    cli_logger.handlers.clear()
    cli_logger.addHandler(handler)
    cli_logger.propagate = False

    # Ensure child loggers inherit from parent
    # This is important for get_logger() to work properly


def get_logger(name: str) -> DjbLogger:
    """Get a DjbLogger instance for the given name."""
    return DjbLogger(name)
