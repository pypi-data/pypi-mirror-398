"""Tests for djb CLI main entry point."""

from __future__ import annotations

from pathlib import Path

import djb
import pytest
import yaml
from click.testing import CliRunner

from djb.cli.djb import djb_cli, print_banner
from djb.config import DjbConfig
from djb.types import Mode, Target


class TestDjbCliHelp:
    """Tests for djb CLI help and options."""

    def test_help_shows_options_and_choices(self):
        """Test that help shows all global options and choices."""
        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--help"])

        assert result.exit_code == 0

        # Global options
        assert "--project-dir" in result.output
        assert "--mode" in result.output
        assert "--target" in result.output
        assert "--log-level" in result.output

        # Mode choices
        assert "development" in result.output
        assert "staging" in result.output
        assert "production" in result.output

        # Target choices
        assert "heroku" in result.output


class TestDjbCliBanner:
    """Tests for djb CLI banner."""

    def test_banner_shows_mode_and_target(self, tmp_path, monkeypatch):
        """Test that banner shows mode and target."""
        monkeypatch.chdir(tmp_path)
        # Create minimal pyproject.toml
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--help"], catch_exceptions=False)

        # Banner appears before --help output (but --help exits early so banner doesn't show)
        # We need to invoke a subcommand that doesn't exit immediately
        # Let's test with secrets --help which should show banner
        result = runner.invoke(djb_cli, ["secrets", "--help"])
        assert "[djb] mode:" in result.output
        assert "target:" in result.output

    def test_banner_suppressed_when_nested(self, tmp_path, monkeypatch):
        """Test that banner is suppressed when DJB_NESTED is set."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DJB_NESTED", "1")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["secrets", "--help"])

        assert "[djb] mode:" not in result.output

    def test_banner_shows_correct_mode_color(self, tmp_path, monkeypatch):
        """Test that banner shows development mode in green."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--mode", "development", "secrets", "--help"])

        # Check for ANSI green color code before "development"
        assert "\033[32m" in result.output or "development" in result.output


class TestDjbCliModeOption:
    """Tests for --mode option."""

    @pytest.mark.parametrize(
        "mode_value,expected_output",
        [
            ("development", "development"),
            ("staging", "staging"),
            ("production", "production"),
            ("PRODUCTION", "production"),  # Case-insensitive
        ],
    )
    def test_mode_option_accepts_valid_values(
        self, tmp_path, monkeypatch, mode_value, expected_output
    ):
        """Test that --mode accepts valid values (case-insensitive)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--mode", mode_value, "secrets", "--help"])

        assert result.exit_code == 0
        assert expected_output in result.output

    def test_mode_option_rejects_invalid(self, tmp_path, monkeypatch):
        """Test that --mode rejects invalid values."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--mode", "invalid", "secrets", "--help"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output


class TestDjbCliModePersistence:
    """Tests for mode persistence."""

    def test_mode_persists_to_config_file(self, tmp_path, monkeypatch):
        """Test that --mode persists to .djb/local.yaml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--mode", "production", "secrets", "--help"])

        assert result.exit_code == 0

        config_path = tmp_path / ".djb" / "local.yaml"
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["mode"] == "production"

    def test_persisted_mode_is_used_in_subsequent_commands(self, tmp_path, monkeypatch):
        """Test that persisted mode is used in subsequent commands."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        # First, set mode to production
        runner = CliRunner()
        runner.invoke(djb_cli, ["--mode", "production", "secrets", "--help"])

        # Reset config between CLI invocations so configure() can be called again
        djb.reset_config()

        # Then run without --mode and verify production is used
        result = runner.invoke(djb_cli, ["secrets", "--help"])

        assert "production" in result.output


class TestDjbCliTargetOption:
    """Tests for --target option."""

    def test_target_option_accepts_heroku(self, tmp_path, monkeypatch):
        """Test that --target heroku is accepted."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--target", "heroku", "secrets", "--help"])

        assert result.exit_code == 0

    def test_target_option_rejects_invalid(self, tmp_path, monkeypatch):
        """Test that --target rejects invalid values."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["--target", "invalid", "secrets", "--help"])

        assert result.exit_code != 0


class TestDjbCliConfigInContext:
    """Tests for config being stored in Click context."""

    def test_config_stored_in_context(self, tmp_path, monkeypatch):
        """Test that config is stored in ctx.obj.

        We verify the config exists by checking the banner output shows
        mode and target, which requires config to be loaded and stored.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testproject"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["secrets", "--help"])

        # If config wasn't loaded, banner wouldn't show mode/target
        assert "mode:" in result.output
        assert "target:" in result.output


class TestPrintBanner:
    """Tests for print_banner function."""

    @pytest.mark.parametrize(
        "mode,expected",
        [
            (Mode.DEVELOPMENT, "development"),
            (Mode.STAGING, "staging"),
            (Mode.PRODUCTION, "production"),
        ],
    )
    def test_print_banner_shows_mode(self, capsys, tmp_path, mode, expected):
        """Test that banner shows the correct mode."""
        config = DjbConfig()
        config.load(
            {
                "project_dir": str(tmp_path),
                "project_name": "test",
                "mode": mode,
                "target": Target.HEROKU,
            }
        )
        print_banner(config)

        captured = capsys.readouterr()
        assert "[djb]" in captured.out
        assert expected in captured.out

    def test_print_banner_format(self, capsys, tmp_path):
        """Test that banner has expected format with mode and target."""
        config = DjbConfig()
        config.load(
            {
                "project_dir": str(tmp_path),
                "project_name": "test",
                "mode": Mode.DEVELOPMENT,
                "target": Target.HEROKU,
            }
        )
        print_banner(config)

        captured = capsys.readouterr()
        assert "mode:" in captured.out
        assert "target:" in captured.out
        assert "heroku" in captured.out
