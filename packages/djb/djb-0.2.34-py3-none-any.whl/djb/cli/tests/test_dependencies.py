"""Tests for djb dependencies command."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from djb.cli.djb import djb_cli


@pytest.fixture
def mock_run_streaming():
    """Mock run_streaming to avoid running actual commands.

    Returns a mock that can be configured per test. Default return is success (0, "", "").
    """
    with patch("djb.cli.dependencies.run_streaming") as mock:
        mock.return_value = (0, "", "")
        yield mock


class TestDjbDependencies:
    """Tests for djb dependencies command."""

    def test_dependencies_help(self, runner):
        """Test that dependencies --help works."""
        result = runner.invoke(djb_cli, ["dependencies", "--help"])
        assert result.exit_code == 0
        assert "Refresh dependencies" in result.output
        assert "--bump" in result.output

    def test_dependencies_requires_scope(self, runner):
        """Test that dependencies requires --frontend or --backend."""
        result = runner.invoke(djb_cli, ["dependencies"])
        assert result.exit_code == 1
        assert "Specify --frontend and/or --backend" in result.output


class TestBackendDependencies:
    """Tests for backend dependency refresh (--backend)."""

    def test_backend_runs_uv_lock_and_sync(self, runner, tmp_path, mock_run_streaming):
        """Test that --backend runs uv lock --upgrade followed by uv sync."""
        result = runner.invoke(djb_cli, ["--backend", "dependencies"])

        assert result.exit_code == 0
        assert mock_run_streaming.call_count == 2

        # First call: uv lock --upgrade
        first_call = mock_run_streaming.call_args_list[0]
        assert first_call.args[0] == ["uv", "lock", "--upgrade"]
        assert first_call.kwargs["cwd"] == tmp_path
        assert first_call.kwargs["label"] == "uv lock"

        # Second call: uv sync
        second_call = mock_run_streaming.call_args_list[1]
        assert second_call.args[0] == ["uv", "sync"]
        assert second_call.kwargs["cwd"] == tmp_path
        assert second_call.kwargs["label"] == "uv sync"

    def test_backend_with_bump_adds_latest_flag(self, runner, tmp_path, mock_run_streaming):
        """Test that --bump adds --latest to uv lock."""
        result = runner.invoke(djb_cli, ["--backend", "dependencies", "--bump"])

        assert result.exit_code == 0
        assert mock_run_streaming.call_count == 2

        # First call should have --latest
        first_call = mock_run_streaming.call_args_list[0]
        assert first_call.args[0] == ["uv", "lock", "--upgrade", "--latest"]

    def test_backend_uv_lock_failure_raises_error(self, runner, mock_run_streaming):
        """Test that uv lock failure raises ClickException."""
        mock_run_streaming.return_value = (1, "", "error output")

        result = runner.invoke(djb_cli, ["--backend", "dependencies"])

        assert result.exit_code == 1
        assert "uv lock failed" in result.output

    def test_backend_uv_sync_failure_raises_error(self, runner, mock_run_streaming):
        """Test that uv sync failure raises ClickException."""
        # First call succeeds (uv lock), second call fails (uv sync)
        mock_run_streaming.side_effect = [(0, "", ""), (1, "", "sync error")]

        result = runner.invoke(djb_cli, ["--backend", "dependencies"])

        assert result.exit_code == 1
        assert "uv sync failed" in result.output

    def test_backend_shows_progress_message(self, runner, mock_run_streaming):
        """Test that backend refresh shows informative progress messages."""
        result = runner.invoke(djb_cli, ["--backend", "dependencies"])

        assert result.exit_code == 0
        assert "Refreshing Python deps with uv" in result.output
        assert "bump=no" in result.output

    def test_backend_with_bump_shows_bump_status(self, runner, mock_run_streaming):
        """Test that --bump shows bump=yes in progress message."""
        result = runner.invoke(djb_cli, ["--backend", "dependencies", "--bump"])

        assert result.exit_code == 0
        assert "bump=yes" in result.output


class TestFrontendDependencies:
    """Tests for frontend dependency refresh (--frontend)."""

    def test_frontend_runs_bun_refresh_deps(self, runner, tmp_path, mock_run_streaming):
        """Test that --frontend runs bun run refresh-deps in frontend directory."""
        result = runner.invoke(djb_cli, ["--frontend", "dependencies"])

        assert result.exit_code == 0
        assert mock_run_streaming.call_count == 1

        call = mock_run_streaming.call_args_list[0]
        assert call.args[0] == ["bun", "run", "refresh-deps"]
        assert call.kwargs["cwd"] == tmp_path / "frontend"
        assert call.kwargs["label"] == "frontend refresh-deps"

    def test_frontend_with_bump_adds_bump_flag(self, runner, tmp_path, mock_run_streaming):
        """Test that --bump adds --bump to bun run refresh-deps."""
        result = runner.invoke(djb_cli, ["--frontend", "dependencies", "--bump"])

        assert result.exit_code == 0

        call = mock_run_streaming.call_args_list[0]
        assert call.args[0] == ["bun", "run", "refresh-deps", "--bump"]

    def test_frontend_failure_raises_error(self, runner, mock_run_streaming):
        """Test that frontend refresh-deps failure raises ClickException."""
        mock_run_streaming.return_value = (1, "", "bun error")

        result = runner.invoke(djb_cli, ["--frontend", "dependencies"])

        assert result.exit_code == 1
        assert "frontend refresh-deps failed" in result.output

    def test_frontend_shows_progress_message(self, runner, mock_run_streaming):
        """Test that frontend refresh shows informative progress messages."""
        result = runner.invoke(djb_cli, ["--frontend", "dependencies"])

        assert result.exit_code == 0
        assert "Refreshing frontend deps with Bun" in result.output
        assert "bump=no" in result.output

    def test_frontend_with_bump_shows_bump_status(self, runner, mock_run_streaming):
        """Test that --bump shows bump=yes in progress message."""
        result = runner.invoke(djb_cli, ["--frontend", "dependencies", "--bump"])

        assert result.exit_code == 0
        assert "bump=yes" in result.output


class TestBothScopes:
    """Tests for running both backend and frontend dependencies."""

    def test_both_scopes_runs_all_commands(self, runner, tmp_path, mock_run_streaming):
        """Test that --backend --frontend runs all dependency commands."""
        result = runner.invoke(djb_cli, ["--backend", "--frontend", "dependencies"])

        assert result.exit_code == 0
        # Backend: uv lock + uv sync, Frontend: bun run refresh-deps
        assert mock_run_streaming.call_count == 3

        # Verify backend commands
        assert mock_run_streaming.call_args_list[0].args[0] == ["uv", "lock", "--upgrade"]
        assert mock_run_streaming.call_args_list[1].args[0] == ["uv", "sync"]

        # Verify frontend command
        assert mock_run_streaming.call_args_list[2].args[0] == ["bun", "run", "refresh-deps"]
        assert mock_run_streaming.call_args_list[2].kwargs["cwd"] == tmp_path / "frontend"

    def test_both_scopes_with_bump(self, runner, mock_run_streaming):
        """Test that --bump applies to both backend and frontend."""
        result = runner.invoke(djb_cli, ["--backend", "--frontend", "dependencies", "--bump"])

        assert result.exit_code == 0

        # Backend should have --latest
        assert mock_run_streaming.call_args_list[0].args[0] == [
            "uv",
            "lock",
            "--upgrade",
            "--latest",
        ]

        # Frontend should have --bump
        assert mock_run_streaming.call_args_list[2].args[0] == [
            "bun",
            "run",
            "refresh-deps",
            "--bump",
        ]

    def test_backend_failure_stops_before_frontend(self, runner, mock_run_streaming):
        """Test that backend failure prevents frontend from running."""
        mock_run_streaming.return_value = (1, "", "uv lock error")

        result = runner.invoke(djb_cli, ["--backend", "--frontend", "dependencies"])

        assert result.exit_code == 1
        # Only uv lock should have been called before failure
        assert mock_run_streaming.call_count == 1
