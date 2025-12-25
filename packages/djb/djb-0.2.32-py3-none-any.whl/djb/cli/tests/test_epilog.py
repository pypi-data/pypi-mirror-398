"""Tests for CLI epilog generation."""

from __future__ import annotations

from djb.cli.epilog import get_cli_epilog


class TestGetCliEpilog:
    """Tests for get_cli_epilog function."""

    def test_returns_string(self):
        """get_cli_epilog should return a string."""
        result = get_cli_epilog()
        assert isinstance(result, str)

    def test_starts_with_formatting_marker(self):
        """Result should start with \\b for Click formatting preservation."""
        result = get_cli_epilog()
        assert result.startswith("\b")

    def test_contains_intro_text(self):
        """Result should contain the intro text."""
        result = get_cli_epilog()
        assert "For deployment, health checks, and secrets operations" in result

    def test_contains_djb_commands(self):
        """Result should list djb commands."""
        result = get_cli_epilog()
        # Check for some known commands
        assert "djb health" in result
        assert "djb deploy" in result
        assert "djb secrets" in result
        assert "djb init" in result
        assert "djb seed" in result

    def test_contains_help_reference(self):
        """Result should reference djb --help for more info."""
        result = get_cli_epilog()
        assert "djb --help" in result

    def test_commands_are_formatted_with_descriptions(self):
        """Each command should have a description."""
        result = get_cli_epilog()
        lines = result.split("\n")
        # Find lines that start with "  djb " (command lines)
        command_lines = [line for line in lines if line.startswith("  djb ")]
        assert len(command_lines) > 0
        # Each command line should have text after the command name
        for line in command_lines:
            # Format is "  djb {name:24} {help_text}"
            # So after "djb " there should be more than just whitespace
            parts = line.split()
            assert len(parts) >= 3, f"Command line missing description: {line}"
