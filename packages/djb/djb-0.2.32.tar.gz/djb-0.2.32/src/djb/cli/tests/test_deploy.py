"""Tests for djb deploy CLI commands."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, Mock, patch

import click
import pytest

from djb.cli.djb import djb_cli


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repository structure."""
    (tmp_path / ".git").mkdir()
    return tmp_path


def _make_streaming_side_effect():
    """Create a side_effect function for run_streaming mock.

    run_streaming returns different values based on combine_output:
    - combine_output=True: (returncode, combined_output)
    - combine_output=False (default): (returncode, stdout, stderr)
    """

    def side_effect(cmd, cwd=None, label=None, combine_output=False):
        if combine_output:
            return (0, "")
        return (0, "", "")

    return side_effect


@pytest.fixture
def mock_deploy_context(tmp_path):
    """Mock subprocess.run, run_streaming, and Path.cwd for deploy tests.

    Yields (mock_subprocess, mock_streaming) tuple for configuring in tests.
    Default setup: subprocess returns success with "main" branch.
    Streaming mock returns appropriate values based on combine_output kwarg.
    """
    with (
        patch("djb.cli.deploy.subprocess.run") as mock_subprocess,
        patch("djb.cli.deploy.run_streaming") as mock_streaming,
        patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
    ):
        mock_subprocess.return_value = Mock(returncode=0, stdout="main\n", stderr="")
        mock_streaming.side_effect = _make_streaming_side_effect()
        yield mock_subprocess, mock_streaming


def make_revert_side_effect(
    *,
    rev_parse_stdout: str = "abc1234567890\n",
    cat_file_stdout: str = "commit\n",
    cat_file_returncode: int = 0,
    log_stdout: str = "abc1234 Some commit\n",
) -> Callable:
    """Factory for creating revert command side_effect functions.

    Args:
        rev_parse_stdout: Output for git rev-parse command
        cat_file_stdout: Output for git cat-file command
        cat_file_returncode: Return code for git cat-file (1 for invalid hash)
        log_stdout: Output for git log command
    """

    def side_effect(cmd, *args, **kwargs):
        if cmd == ["heroku", "auth:whoami"]:
            return Mock(returncode=0)
        if "rev-parse" in cmd:
            return Mock(returncode=0, stdout=rev_parse_stdout)
        if "cat-file" in cmd:
            return Mock(returncode=cat_file_returncode, stdout=cat_file_stdout, stderr="")
        if "log" in cmd:
            return Mock(returncode=0, stdout=log_stdout)
        return Mock(returncode=0, stdout="", stderr="")

    return side_effect


class TestDeployHerokuCommand:
    """Tests for deploy heroku CLI command."""

    def test_help(self, runner):
        """Test that deploy heroku --help works."""
        result = runner.invoke(djb_cli, ["deploy", "heroku", "--help"])
        assert result.exit_code == 0
        assert "Deploy to Heroku" in result.output
        assert "deploys the application to Heroku" in result.output
        assert "--app" in result.output
        assert "--local-build" in result.output
        assert "--skip-migrate" in result.output
        assert "--skip-secrets" in result.output
        # Verify subcommands are listed
        assert "setup" in result.output
        assert "revert" in result.output

    def test_uses_derived_project_name_when_not_configured(self, runner, tmp_path, monkeypatch):
        """Test that project_name is derived from directory name when not configured."""
        # Run in a temp directory with no project name configured
        monkeypatch.chdir(tmp_path)
        # Create minimal pyproject.toml without project name
        (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []\n")
        # Clear the env var set by conftest fixture
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)

        result = runner.invoke(djb_cli, ["deploy", "heroku"])
        # With the new behavior, project_name is always derived from directory name
        # so the command should proceed (and fail for other reasons, like missing git)
        # but not fail due to missing project_name
        assert "Missing required config: project_name" not in result.output

    def test_editable_djb_handling(self, runner, tmp_path):
        """Test that editable djb is temporarily stashed for deploy."""
        # Create project structure
        (tmp_path / ".git").mkdir()
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        (djb_dir / "pyproject.toml").write_text('name = "djb"')

        # Create pyproject.toml with editable djb
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.sources]
djb = { path = "./djb", editable = true }
"""
        )

        # Create uv.lock to be stashed
        uv_lock = tmp_path / "uv.lock"
        uv_lock.write_text('[[package]]\nname = "djb"\nsource = { editable = "djb" }\n')

        with (
            patch("djb.cli.deploy.subprocess.run") as deploy_mock,
            patch("djb.cli.deploy.run_streaming") as streaming_mock,
            patch("djb.cli.editable_stash.subprocess.run") as stash_mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            # Set up mocks
            deploy_mock.return_value = Mock(returncode=0, stdout="main\n", stderr="")
            streaming_mock.side_effect = _make_streaming_side_effect()
            stash_mock.return_value = Mock(returncode=0, stdout="", stderr="")

            result = runner.invoke(djb_cli, ["deploy", "heroku", "--app", "testapp", "-y"])

        # Should have stashed and restored editable djb configuration
        assert "Stashed editable djb configuration for deploy" in result.output
        assert "Restoring editable djb configuration" in result.output

    def test_local_build_option(self, runner, git_repo, mock_deploy_context):
        """Test --local-build runs frontend build locally."""
        frontend_dir = git_repo / "frontend"
        frontend_dir.mkdir()

        result = runner.invoke(
            djb_cli, ["deploy", "heroku", "--app", "testapp", "--local-build", "-y"]
        )

        assert "Building frontend assets locally" in result.output

    def test_skip_migrate_option(self, runner, git_repo, mock_deploy_context):
        """Test --skip-migrate skips database migrations."""
        result = runner.invoke(
            djb_cli, ["deploy", "heroku", "--app", "testapp", "--skip-migrate", "-y"]
        )

        assert "Database migrations" in result.output  # logger.skip() format

    def test_skip_secrets_option(self, runner, git_repo, mock_deploy_context):
        """Test --skip-secrets skips secrets sync."""
        result = runner.invoke(
            djb_cli, ["deploy", "heroku", "--app", "testapp", "--skip-secrets", "-y"]
        )

        assert "Secrets sync" in result.output  # logger.skip() format

    def test_requires_git_repository(self, runner, tmp_path):
        """Test that deploy requires a git repository."""
        # No .git directory
        with patch("djb.cli.deploy.Path.cwd", return_value=tmp_path):
            with patch("djb.cli.deploy.subprocess.run") as mock:
                mock.return_value = Mock(returncode=0, stdout="", stderr="")

                result = runner.invoke(djb_cli, ["deploy", "heroku", "--app", "testapp", "-y"])

        assert result.exit_code == 1
        assert "Not in a git repository" in result.output

    def test_mode_guard_warns_when_not_production(self, runner, git_repo, mock_deploy_context):
        """Test that deployment warns when mode is not production."""
        # Deploy with default mode (development) and confirm the prompt
        result = runner.invoke(djb_cli, ["deploy", "heroku", "--app", "testapp"], input="y\n")

        assert "Deploying to Heroku with mode=development" in result.output
        assert "Set production mode: djb --mode production deploy heroku" in result.output

    def test_mode_guard_can_cancel_deployment(self, runner, git_repo, tmp_path):
        """Test that deployment can be cancelled when mode is not production."""
        with (
            patch("djb.cli.deploy.subprocess.run") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.return_value = Mock(returncode=0, stdout="", stderr="")

            # Deploy with default mode (development) and decline the prompt
            result = runner.invoke(djb_cli, ["deploy", "heroku", "--app", "testapp"], input="n\n")

        assert result.exit_code == 1
        assert "Deployment cancelled" in result.output

    def test_mode_guard_yes_flag_skips_confirmation(self, runner, git_repo, mock_deploy_context):
        """Test that -y flag skips mode confirmation prompt."""
        # Deploy with -y flag should not prompt for mode confirmation
        result = runner.invoke(djb_cli, ["deploy", "heroku", "--app", "testapp", "-y"])

        # Should show warning but not prompt
        assert "Deploying to Heroku with mode=development" in result.output
        # Should proceed without user input
        assert "Continue with deployment?" not in result.output

    def test_mode_guard_no_warning_when_production(self, runner, git_repo, mock_deploy_context):
        """Test that no mode warning is shown when mode is production."""
        # Create config directory with production mode
        config_dir = git_repo / ".djb"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("mode: production\n")

        # Use -y to skip other prompts (uncommitted changes, etc.)
        result = runner.invoke(
            djb_cli, ["--mode", "production", "deploy", "heroku", "--app", "testapp", "-y"]
        )

        # Should not show mode warning (the mode guard should not trigger)
        assert "Deploying to Heroku with mode=" not in result.output


class TestDeployHerokuRevertCommand:
    """Tests for deploy heroku revert CLI command."""

    def test_help(self, runner):
        """Test that deploy heroku revert --help works."""
        result = runner.invoke(djb_cli, ["deploy", "heroku", "revert", "--help"])
        assert result.exit_code == 0
        assert "Revert to a previous deployment" in result.output
        assert "--skip-migrate" in result.output

    def test_uses_derived_project_name_when_not_configured(self, runner, tmp_path, monkeypatch):
        """Test that project_name is derived from directory name when not configured."""
        # Run in a temp directory with no project name configured
        monkeypatch.chdir(tmp_path)
        # Create minimal pyproject.toml without project name
        (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []\n")
        # Clear the env var set by conftest fixture
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)

        result = runner.invoke(djb_cli, ["deploy", "heroku", "revert"])
        # With the new behavior, project_name is always derived from directory name
        # so the command should proceed (and fail for other reasons, like missing git)
        # but not fail due to missing project_name
        assert "Missing required config: project_name" not in result.output

    def test_revert_to_previous_commit(self, runner, git_repo, tmp_path):
        """Test reverting to previous commit (HEAD~1)."""
        with (
            patch("djb.cli.deploy.subprocess.run") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.side_effect = make_revert_side_effect(log_stdout="abc1234 Previous commit\n")

            result = runner.invoke(
                djb_cli, ["deploy", "heroku", "--app", "testapp", "revert"], input="y\n"
            )

        assert "No git hash provided, using previous commit" in result.output

    def test_revert_to_specific_commit(self, runner, git_repo, tmp_path):
        """Test reverting to a specific commit hash."""
        with (
            patch("djb.cli.deploy.subprocess.run") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.side_effect = make_revert_side_effect(log_stdout="def5678 Specific commit\n")

            result = runner.invoke(
                djb_cli, ["deploy", "heroku", "--app", "testapp", "revert", "def5678"], input="y\n"
            )

        assert "Reverting to: def5678" in result.output

    def test_revert_invalid_hash(self, runner, git_repo, tmp_path):
        """Test revert with invalid git hash."""
        with (
            patch("djb.cli.deploy.subprocess.run") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.side_effect = make_revert_side_effect(cat_file_returncode=1)

            result = runner.invoke(
                djb_cli, ["deploy", "heroku", "--app", "testapp", "revert", "invalid"]
            )

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_revert_cancelled(self, runner, git_repo, tmp_path):
        """Test revert can be cancelled at confirmation."""
        with (
            patch("djb.cli.deploy.subprocess.run") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.side_effect = make_revert_side_effect()

            result = runner.invoke(
                djb_cli, ["deploy", "heroku", "--app", "testapp", "revert"], input="n\n"
            )

        assert result.exit_code == 1
        assert "Revert cancelled" in result.output

    def test_revert_skip_migrate(self, runner, git_repo, tmp_path):
        """Test revert with --skip-migrate skips migrations."""
        with (
            patch("djb.cli.deploy.subprocess.run") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.side_effect = make_revert_side_effect()

            result = runner.invoke(
                djb_cli,
                ["deploy", "heroku", "--app", "testapp", "revert", "--skip-migrate"],
                input="y\n",
            )

        assert "Database migrations" in result.output  # logger.skip() format


class TestDeployHerokuSeedCommand:
    """Tests for deploy heroku seed CLI command."""

    def test_help_unconfigured(self, runner, monkeypatch, tmp_path):
        """Test that help shows configuration instructions when no seed_command is configured."""
        # Clear seed_command config
        monkeypatch.setenv("DJB_SEED_COMMAND", "")

        mock_config = MagicMock()
        mock_config.seed_command = None

        with patch("djb.cli.deploy.config", mock_config):
            result = runner.invoke(djb_cli, ["deploy", "heroku", "seed", "--help"])

        assert result.exit_code == 0
        assert "Run the host project's seed command on Heroku" in result.output
        assert "WARNING: This modifies the production database on Heroku!" in result.output
        assert "No seed_command is currently configured" in result.output
        assert "djb config seed_command" in result.output

    def test_help_configured(self, runner):
        """Test that help shows djb options plus host command help when seed_command is configured."""

        # Create a mock host command with help text
        @click.command()
        @click.option("--truncate", is_flag=True, help="Clear database before seeding")
        def mock_seed(truncate):
            """A test seed command for the database."""

        mock_config = MagicMock()
        mock_config.seed_command = "myapp.cli:seed"

        with (
            patch("djb.cli.deploy.config", mock_config),
            patch("djb.cli.deploy.load_seed_command") as mock_load,
        ):
            mock_load.return_value = mock_seed

            result = runner.invoke(djb_cli, ["deploy", "heroku", "seed", "--help"])

        assert result.exit_code == 0
        # Check djb command's own help is shown
        assert "Run seed command on Heroku" in result.output
        assert "--here-be-dragons" in result.output
        assert "--app" in result.output
        # Check host command help is appended
        assert "Configured seed command: myapp.cli:seed" in result.output
        assert "--- Host command help ---" in result.output
        assert "A test seed command for the database" in result.output

    def test_requires_here_be_dragons(self, runner):
        """Test that --here-be-dragons is required."""
        result = runner.invoke(djb_cli, ["deploy", "heroku", "--app", "testapp", "seed"])
        assert result.exit_code != 0
        assert "Missing option '--here-be-dragons'" in result.output

    def test_builds_correct_heroku_command(self, runner, git_repo, tmp_path):
        """Test that seed builds correct heroku run command."""
        with (
            patch("djb.cli.deploy.run_streaming") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.return_value = (0, "", "")

            result = runner.invoke(
                djb_cli,
                ["deploy", "heroku", "--app", "testapp", "seed", "--here-be-dragons"],
            )

        assert result.exit_code == 0
        # Verify the heroku run command was called correctly
        call_args = mock.call_args[0][0]
        assert call_args == [
            "heroku",
            "run",
            "--no-notify",
            "--app",
            "testapp",
            "--",
            "djb",
            "seed",
        ]

    def test_extra_args_passed_to_seed(self, runner, git_repo, tmp_path):
        """Test that extra args (like --truncate) are passed through to djb seed."""
        with (
            patch("djb.cli.deploy.run_streaming") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.return_value = (0, "", "")

            result = runner.invoke(
                djb_cli,
                [
                    "deploy",
                    "heroku",
                    "--app",
                    "testapp",
                    "seed",
                    "--here-be-dragons",
                    "--",
                    "--truncate",
                ],
            )

        assert result.exit_code == 0
        call_args = mock.call_args[0][0]
        assert call_args == [
            "heroku",
            "run",
            "--no-notify",
            "--app",
            "testapp",
            "--",
            "djb",
            "seed",
            "--truncate",
        ]

    def test_inherits_app_from_parent(self, runner, git_repo, tmp_path):
        """Test that app is inherited from parent heroku command."""
        with (
            patch("djb.cli.deploy.run_streaming") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.return_value = (0, "", "")

            result = runner.invoke(
                djb_cli,
                ["deploy", "heroku", "--app", "parentapp", "seed", "--here-be-dragons"],
            )

        assert result.exit_code == 0
        call_args = mock.call_args[0][0]
        assert "parentapp" in call_args

    def test_heroku_command_failure(self, runner, git_repo, tmp_path):
        """Test that heroku run failure is reported."""
        with (
            patch("djb.cli.deploy.run_streaming") as mock,
            patch("djb.cli.deploy.Path.cwd", return_value=tmp_path),
        ):
            mock.return_value = (1, "", "")

            result = runner.invoke(
                djb_cli,
                ["deploy", "heroku", "--app", "testapp", "seed", "--here-be-dragons"],
            )

        assert result.exit_code == 1
        assert "Heroku seed failed with exit code 1" in result.output


class TestDeployGroup:
    """Tests for deploy command group."""

    def test_deploy_help(self, runner):
        """Test that deploy --help shows subcommands."""
        result = runner.invoke(djb_cli, ["deploy", "--help"])
        assert result.exit_code == 0
        assert "heroku" in result.output
        # revert is now under heroku, not deploy
        assert "revert" not in result.output
