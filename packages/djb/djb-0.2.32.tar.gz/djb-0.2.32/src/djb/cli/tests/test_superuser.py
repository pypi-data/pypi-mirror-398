"""Tests for djb sync-superuser CLI command."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from djb.cli.djb import djb_cli


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to avoid actual command execution."""
    with patch("djb.cli.superuser.subprocess.run") as mock:
        mock.return_value = Mock(returncode=0)
        yield mock


@pytest.fixture
def mock_run_streaming():
    """Mock run_streaming for Heroku commands."""
    with patch("djb.cli.superuser.run_streaming") as mock:
        mock.return_value = (0, "", "")
        yield mock


class TestSyncSuperuserCommand:
    """Tests for sync-superuser CLI command."""

    def test_help(self, runner):
        """Test that sync-superuser --help works."""
        result = runner.invoke(djb_cli, ["sync-superuser", "--help"])
        assert result.exit_code == 0
        assert "Sync superuser from encrypted secrets" in result.output
        assert "--environment" in result.output
        assert "--dry-run" in result.output
        assert "--app" in result.output

    def test_local_sync_default(self, runner, mock_subprocess_run):
        """Test local sync with default options."""
        result = runner.invoke(djb_cli, ["sync-superuser"])

        assert result.exit_code == 0
        assert "Syncing superuser locally" in result.output

        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args == ["python", "manage.py", "sync_superuser"]

    def test_local_sync_with_environment(self, runner, mock_subprocess_run):
        """Test local sync with specific environment."""
        result = runner.invoke(djb_cli, ["sync-superuser", "-e", "dev"])

        assert result.exit_code == 0
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args == ["python", "manage.py", "sync_superuser", "--environment", "dev"]

    def test_local_sync_with_dry_run(self, runner, mock_subprocess_run):
        """Test local sync with dry-run flag."""
        result = runner.invoke(djb_cli, ["sync-superuser", "--dry-run"])

        assert result.exit_code == 0
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args == ["python", "manage.py", "sync_superuser", "--dry-run"]

    def test_local_sync_with_all_options(self, runner, mock_subprocess_run):
        """Test local sync with all options combined."""
        result = runner.invoke(djb_cli, ["sync-superuser", "-e", "staging", "--dry-run"])

        assert result.exit_code == 0
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args == [
            "python",
            "manage.py",
            "sync_superuser",
            "--environment",
            "staging",
            "--dry-run",
        ]

    def test_heroku_sync(self, runner, mock_run_streaming):
        """Test sync on Heroku."""
        result = runner.invoke(djb_cli, ["sync-superuser", "--app", "myapp"])

        assert result.exit_code == 0
        mock_run_streaming.assert_called_once()
        call_args = mock_run_streaming.call_args[0][0]
        call_kwargs = mock_run_streaming.call_args[1]
        assert call_args == [
            "heroku",
            "run",
            "--no-notify",
            "--app",
            "myapp",
            "--",
            "python",
            "manage.py",
            "sync_superuser",
        ]
        assert call_kwargs["label"] == "Syncing superuser on Heroku (myapp)"

    def test_heroku_sync_with_environment(self, runner, mock_run_streaming):
        """Test Heroku sync with specific environment."""
        result = runner.invoke(djb_cli, ["sync-superuser", "--app", "myapp", "-e", "production"])

        assert result.exit_code == 0
        call_args = mock_run_streaming.call_args[0][0]
        assert call_args == [
            "heroku",
            "run",
            "--no-notify",
            "--app",
            "myapp",
            "--",
            "python",
            "manage.py",
            "sync_superuser",
            "--environment",
            "production",
        ]

    def test_heroku_sync_with_dry_run(self, runner, mock_run_streaming):
        """Test Heroku sync with dry-run."""
        result = runner.invoke(djb_cli, ["sync-superuser", "--app", "myapp", "--dry-run"])

        assert result.exit_code == 0
        call_args = mock_run_streaming.call_args[0][0]
        assert "--dry-run" in call_args

    def test_heroku_sync_with_all_options(self, runner, mock_run_streaming):
        """Test Heroku sync with all options."""
        result = runner.invoke(
            djb_cli, ["sync-superuser", "--app", "myapp", "-e", "production", "--dry-run"]
        )

        assert result.exit_code == 0
        call_args = mock_run_streaming.call_args[0][0]
        assert call_args == [
            "heroku",
            "run",
            "--no-notify",
            "--app",
            "myapp",
            "--",
            "python",
            "manage.py",
            "sync_superuser",
            "--environment",
            "production",
            "--dry-run",
        ]

    def test_failure_returns_error(self, runner, mock_subprocess_run):
        """Test that command failure raises ClickException."""
        mock_subprocess_run.return_value = Mock(returncode=1)

        result = runner.invoke(djb_cli, ["sync-superuser"])

        assert result.exit_code == 1
        assert "Failed to sync superuser" in result.output

    def test_heroku_failure_returns_error(self, runner, mock_run_streaming):
        """Test that Heroku command failure raises ClickException."""
        mock_run_streaming.return_value = (1, "", "")

        result = runner.invoke(djb_cli, ["sync-superuser", "--app", "myapp"])

        assert result.exit_code == 1
        assert "Failed to sync superuser" in result.output

    def test_environment_choices(self, runner):
        """Test that only valid environment choices are accepted."""
        result = runner.invoke(djb_cli, ["sync-superuser", "-e", "invalid_env"])

        assert result.exit_code == 2
        assert "Invalid value" in result.output or "invalid_env" in result.output

    @pytest.mark.parametrize("environment", ["dev", "staging", "production"])
    def test_valid_environment(self, runner, mock_subprocess_run, environment):
        """Test that valid environments are accepted."""
        result = runner.invoke(djb_cli, ["sync-superuser", "-e", environment])
        assert result.exit_code == 0
