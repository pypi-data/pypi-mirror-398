"""Tests for djb seed CLI command."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import click

from djb.cli.djb import djb_cli


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
