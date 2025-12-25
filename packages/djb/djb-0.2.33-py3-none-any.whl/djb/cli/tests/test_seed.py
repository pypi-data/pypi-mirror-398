"""Tests for djb seed CLI command."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, Mock, patch

import click
import pytest

from djb.cli.djb import djb_cli
from djb.cli.seed import load_seed_command, run_seed_command


class TestSeedCommand:
    """Tests for seed CLI command."""

    def test_help_unconfigured(self, runner):
        """Test that help shows configuration instructions when no seed_command is configured."""
        mock_config = MagicMock()
        mock_config.seed_command = None

        with patch("djb.cli.seed.config", mock_config):
            result = runner.invoke(djb_cli, ["seed", "--help"])

        assert result.exit_code == 0
        assert "Run the host project's seed command" in result.output
        assert "No seed_command is currently configured" in result.output
        assert "djb config seed_command" in result.output
        assert "Example seed command in your project" in result.output

    def test_help_configured(self, runner):
        """Test that help shows host command help when seed_command is configured."""

        # Create a mock host command with help text
        @click.command()
        @click.option("--truncate", is_flag=True, help="Clear database before seeding")
        def mock_seed(truncate):
            """Populate the database with sample data."""

        mock_config = MagicMock()
        mock_config.seed_command = "myapp.cli:seed"

        with (
            patch("djb.cli.seed.config", mock_config),
            patch("djb.cli.seed.load_seed_command") as mock_load,
        ):
            mock_load.return_value = mock_seed

            result = runner.invoke(djb_cli, ["seed", "--help"])

        assert result.exit_code == 0
        assert "Run the host project's seed command" in result.output
        assert "Configured seed command: myapp.cli:seed" in result.output
        assert "--- Host command help ---" in result.output
        assert "Populate the database with sample data" in result.output

    def test_seed_without_config_fails(self, runner, monkeypatch, tmp_path):
        """Test that running seed without config fails with helpful message."""
        # Clear seed_command so CLI sees it as unconfigured
        # Need to clear both env var AND isolate from real project config
        monkeypatch.delenv("DJB_SEED_COMMAND", raising=False)
        # Use tmp_path as project dir to avoid reading real project's config
        monkeypatch.setenv("DJB_PROJECT_DIR", str(tmp_path))

        # Also change working directory to tmp_path to fully isolate from real project
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(djb_cli, ["seed"])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 1
        assert "No seed_command configured" in result.output
        assert "djb config seed_command" in result.output

    def test_seed_with_invalid_config_fails(self, runner, monkeypatch, tmp_path):
        """Test that running seed with invalid module path fails gracefully."""
        # Set invalid seed_command via environment
        monkeypatch.setenv("DJB_SEED_COMMAND", "nonexistent.module:cmd")
        monkeypatch.setenv("DJB_PROJECT_DIR", str(tmp_path))

        with patch("djb.cli.seed.django.setup"):  # Skip Django setup
            result = runner.invoke(djb_cli, ["seed"])

        assert result.exit_code == 1
        assert "Could not load seed_command" in result.output

    def test_seed_runs_host_command(self, runner, monkeypatch, tmp_path):
        """Test that seed invokes the configured host command."""
        invoked = []

        @click.command()
        def mock_seed_cmd():
            """Mock seed command."""
            invoked.append(True)

        monkeypatch.setenv("DJB_SEED_COMMAND", "myapp.cli:seed")
        monkeypatch.setenv("DJB_PROJECT_DIR", str(tmp_path))

        with (
            patch("djb.cli.seed.load_seed_command") as mock_load,
            patch("djb.cli.seed.django.setup"),
        ):
            mock_load.return_value = mock_seed_cmd

            result = runner.invoke(djb_cli, ["seed"])

        assert result.exit_code == 0
        assert invoked == [True], "Host command should have been invoked"

    def test_seed_passes_extra_args_to_host_command(self, runner, monkeypatch, tmp_path):
        """Test that extra arguments are passed to the host command."""
        received_args = {}

        @click.command()
        @click.option("--truncate", is_flag=True)
        @click.option("--count", type=int, default=10)
        def mock_seed_cmd(truncate, count):
            """Mock seed command with options."""
            received_args["truncate"] = truncate
            received_args["count"] = count

        monkeypatch.setenv("DJB_SEED_COMMAND", "myapp.cli:seed")
        monkeypatch.setenv("DJB_PROJECT_DIR", str(tmp_path))

        with (
            patch("djb.cli.seed.load_seed_command") as mock_load,
            patch("djb.cli.seed.django.setup"),
        ):
            mock_load.return_value = mock_seed_cmd

            result = runner.invoke(djb_cli, ["seed", "--truncate", "--count", "50"])

        assert result.exit_code == 0
        assert received_args == {"truncate": True, "count": 50}

    def test_seed_host_command_failure_propagates(self, runner, monkeypatch, tmp_path):
        """Test that host command failures are propagated."""

        @click.command()
        def mock_seed_cmd():
            """Mock seed command that fails."""
            raise click.ClickException("Database connection failed")

        monkeypatch.setenv("DJB_SEED_COMMAND", "myapp.cli:seed")
        monkeypatch.setenv("DJB_PROJECT_DIR", str(tmp_path))

        with (
            patch("djb.cli.seed.load_seed_command") as mock_load,
            patch("djb.cli.seed.django.setup"),
        ):
            mock_load.return_value = mock_seed_cmd

            result = runner.invoke(djb_cli, ["seed"])

        assert result.exit_code == 1
        assert "Database connection failed" in result.output


class TestLoadSeedCommand:
    """Tests for load_seed_command() function directly."""

    def test_load_valid_command(self):
        """Test loading a valid Click command from module:attr format."""
        # Create a mock module with a click command
        mock_command = click.Command(name="test_cmd", callback=lambda: None)
        mock_module = Mock()
        mock_module.my_command = mock_command

        with patch("djb.cli.seed.importlib.import_module", return_value=mock_module):
            result = load_seed_command("mymodule:my_command")

        assert result is mock_command

    def test_load_command_invalid_format_missing_colon(self):
        """Test that invalid format (missing colon) returns None and logs warning."""
        with patch("djb.cli.seed.logger") as mock_logger:
            result = load_seed_command("invalid_format_no_colon")

        assert result is None
        mock_logger.warning.assert_called_once()
        assert "Invalid seed_command format" in mock_logger.warning.call_args[0][0]

    def test_load_command_nonexistent_module(self):
        """Test that non-existent module returns None and logs warning."""
        # Patch logger first to avoid issues with import_module affecting module resolution
        with patch("djb.cli.seed.logger") as mock_logger:
            with patch(
                "djb.cli.seed.importlib.import_module",
                side_effect=ImportError("No module named 'nonexistent'"),
            ):
                result = load_seed_command("nonexistent.module:cmd")

        assert result is None
        mock_logger.warning.assert_called_once()
        assert "Could not import" in mock_logger.warning.call_args[0][0]

    def test_load_command_nonexistent_attribute(self):
        """Test that non-existent attribute returns None and logs warning."""

        class ModuleWithoutAttr:
            """Module mock that raises AttributeError for getattr."""

            pass

        mock_module = ModuleWithoutAttr()

        with patch("djb.cli.seed.logger") as mock_logger:
            with patch("djb.cli.seed.importlib.import_module", return_value=mock_module):
                result = load_seed_command("mymodule:nonexistent_attr")

        assert result is None
        mock_logger.warning.assert_called_once()
        assert "Could not find" in mock_logger.warning.call_args[0][0]

    def test_load_command_not_a_click_command(self):
        """Test that attribute that isn't a Click command returns None."""
        mock_module = Mock()
        mock_module.not_a_command = "just a string"

        with patch("djb.cli.seed.logger") as mock_logger:
            with patch("djb.cli.seed.importlib.import_module", return_value=mock_module):
                result = load_seed_command("mymodule:not_a_command")

        assert result is None
        mock_logger.warning.assert_called_once()
        assert "is not a Click command" in mock_logger.warning.call_args[0][0]

    def test_load_command_handles_callable_that_is_not_command(self):
        """Test that a callable that isn't a Click command returns None."""
        mock_module = Mock()
        mock_module.my_function = lambda: "hello"

        with patch("djb.cli.seed.logger") as mock_logger:
            with patch("djb.cli.seed.importlib.import_module", return_value=mock_module):
                result = load_seed_command("mymodule:my_function")

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_load_command_with_click_group(self):
        """Test that Click groups (which are commands) are loaded successfully."""
        mock_group = click.Group(name="test_group")
        mock_module = Mock()
        mock_module.my_group = mock_group

        with patch("djb.cli.seed.importlib.import_module", return_value=mock_module):
            result = load_seed_command("mymodule:my_group")

        assert result is mock_group


class TestRunSeedCommand:
    """Tests for run_seed_command() function directly."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock DjbConfig."""
        config = MagicMock()
        config.seed_command = None
        return config

    def test_run_seed_no_command_configured(self, mock_config):
        """Test that missing seed_command returns False and logs warning."""
        mock_config.seed_command = None

        with patch("djb.cli.seed.logger") as mock_logger:
            result = run_seed_command(mock_config)

        assert result is False
        mock_logger.warning.assert_called_once()
        assert "No seed_command configured" in mock_logger.warning.call_args[0][0]

    def test_run_seed_load_fails(self, mock_config):
        """Test that load failure returns False."""
        mock_config.seed_command = "bad.module:cmd"

        with patch("djb.cli.seed.load_seed_command", return_value=None):
            result = run_seed_command(mock_config)

        assert result is False

    def test_run_seed_successful_execution(self, mock_config):
        """Test successful command execution returns True."""
        mock_config.seed_command = "myapp.cli:seed"

        invoked = []

        @click.command()
        def mock_seed():
            invoked.append(True)

        with patch("djb.cli.seed.load_seed_command", return_value=mock_seed):
            result = run_seed_command(mock_config)

        assert result is True
        assert invoked == [True]

    def test_run_seed_click_exception_returns_false(self, mock_config):
        """Test that ClickException from host command returns False."""
        mock_config.seed_command = "myapp.cli:seed"

        @click.command()
        def failing_seed():
            raise click.ClickException("Seeding failed")

        with (
            patch("djb.cli.seed.load_seed_command", return_value=failing_seed),
            patch("djb.cli.seed.logger") as mock_logger,
        ):
            result = run_seed_command(mock_config)

        assert result is False
        mock_logger.error.assert_called_once()
        assert "Seed failed" in mock_logger.error.call_args[0][0]
        assert "Seeding failed" in mock_logger.error.call_args[0][0]

    def test_run_seed_generic_exception_returns_false(self, mock_config):
        """Test that generic exception from host command returns False."""
        mock_config.seed_command = "myapp.cli:seed"

        @click.command()
        def crashing_seed():
            raise ValueError("Unexpected error")

        with (
            patch("djb.cli.seed.load_seed_command", return_value=crashing_seed),
            patch("djb.cli.seed.logger") as mock_logger,
        ):
            result = run_seed_command(mock_config)

        assert result is False
        mock_logger.error.assert_called_once()
        assert "Seed failed" in mock_logger.error.call_args[0][0]

    def test_run_seed_command_without_options(self, mock_config):
        """Test that run_seed_command works with simple commands without options."""
        mock_config.seed_command = "myapp.cli:seed"

        invoked = []

        @click.command()
        def simple_seed():
            """A simple seed command without options."""
            invoked.append(True)

        with patch("djb.cli.seed.load_seed_command", return_value=simple_seed):
            result = run_seed_command(mock_config)

        assert result is True
        assert invoked == [True]
