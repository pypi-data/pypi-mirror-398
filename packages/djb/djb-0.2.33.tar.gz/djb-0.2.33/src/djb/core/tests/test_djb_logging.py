"""Tests for djb logging module."""

from __future__ import annotations

import logging
import pytest

from djb import setup_logging, get_logger, Level


class TestLogging:
    """Tests for djb logging utilities."""

    def test_setup_logging_configures_logger(self):
        """Test that setup_logging configures the logger."""
        setup_logging("info")
        logger = get_logger("test")

        # Logger should be configured
        assert logger.logger.level == 0  # Uses parent's level
        parent = logging.getLogger("djb.cli")
        assert parent.level == Level.INFO

    def test_logger_info(self, capfd):
        """Test logger.info() outputs message."""
        setup_logging("info")
        logger = get_logger("test.info")

        logger.info("Test message")

        captured = capfd.readouterr()
        assert "Test message" in captured.out

    def test_logger_done(self, capfd):
        """Test logger.done() outputs message in green."""
        setup_logging("info")
        logger = get_logger("test.done")

        logger.done("Task completed")

        captured = capfd.readouterr()
        assert "Task completed" in captured.out

    def test_logger_skip(self, capfd):
        """Test logger.skip() outputs with skip prefix."""
        setup_logging("info")
        logger = get_logger("test.skip")

        logger.skip("Skipped task")

        captured = capfd.readouterr()
        assert ">> Skipped task" in captured.out

    def test_logger_next(self, capfd):
        """Test logger.next() adds ellipsis."""
        setup_logging("info")
        logger = get_logger("test.next")

        logger.next("Starting task")

        captured = capfd.readouterr()
        assert "Starting task..." in captured.out

    def test_logger_next_preserves_existing_ellipsis(self, capfd):
        """Test logger.next() doesn't double-add ellipsis."""
        setup_logging("info")
        logger = get_logger("test.next.preserve")

        logger.next("Already has ellipsis...")

        captured = capfd.readouterr()
        # Should not have double ellipsis
        assert "Already has ellipsis..." in captured.out
        assert "......" not in captured.out

    def test_logger_error(self, capfd):
        """Test logger.error() outputs message in red."""
        setup_logging("error")
        logger = get_logger("test.error")

        logger.error("Error occurred")

        captured = capfd.readouterr()
        assert "Error occurred" in captured.out

    def test_logger_warning(self, capfd):
        """Test logger.warning() outputs message in yellow."""
        setup_logging("warning")
        logger = get_logger("test.warning")

        logger.warning("Warning message")

        captured = capfd.readouterr()
        assert "Warning message" in captured.out

    def test_logger_debug_hidden_at_info_level(self, capfd):
        """Test logger.debug() is hidden at info level."""
        setup_logging("info")
        logger = get_logger("test.debug")

        logger.debug("Debug message")

        captured = capfd.readouterr()
        assert "Debug message" not in captured.out

    def test_logger_debug_shown_at_debug_level(self, capfd):
        """Test logger.debug() is shown at debug level."""
        setup_logging("debug")
        logger = get_logger("test.debug.shown")

        logger.debug("Debug message")

        captured = capfd.readouterr()
        assert "Debug message" in captured.out

    def test_logger_note(self, capfd):
        """Test logger.note() outputs empty line."""
        setup_logging("note")
        logger = get_logger("test.note")

        logger.note()

        captured = capfd.readouterr()
        # Should output a newline
        assert captured.out == "\n"

    @pytest.mark.parametrize(
        "level_str,expected",
        [
            ("error", Level.ERROR),
            ("warning", Level.WARNING),
            ("info", Level.INFO),
            ("note", Level.NOTE),
            ("debug", Level.DEBUG),
            ("ERROR", Level.ERROR),  # Case-insensitive
            ("Warning", Level.WARNING),  # Case-insensitive
            ("unknown", Level.NOTE),  # Defaults to NOTE
            ("", Level.NOTE),  # Empty defaults to NOTE
        ],
    )
    def test_log_level_from_string(self, level_str, expected):
        """Test Level.from_string() converts strings to log levels."""
        assert Level.from_string(level_str) == expected

    def test_multiple_loggers_share_config(self, capfd):
        """Test that multiple loggers share the same configuration."""
        setup_logging("info")
        logger1 = get_logger("test.logger1")
        logger2 = get_logger("test.logger2")

        logger1.info("Message from logger1")
        logger2.info("Message from logger2")

        captured = capfd.readouterr()
        assert "Message from logger1" in captured.out
        assert "Message from logger2" in captured.out

    def test_verbosity_error_level_filters_info(self, capfd):
        """Test that error level filters out info messages."""
        setup_logging("error")
        logger = get_logger("test.filter")

        logger.info("This should not appear")
        logger.error("This should appear")

        captured = capfd.readouterr()
        assert "This should not appear" not in captured.out
        assert "This should appear" in captured.out

    def test_verbosity_info_level_allows_info_and_errors(self, capfd):
        """Test that info level allows both info and error messages."""
        setup_logging("info")
        logger = get_logger("test.both")

        logger.info("Info message")
        logger.error("Error message")
        logger.debug("Debug message (hidden)")

        captured = capfd.readouterr()
        assert "Info message" in captured.out
        assert "Error message" in captured.out
        assert "Debug message" not in captured.out
