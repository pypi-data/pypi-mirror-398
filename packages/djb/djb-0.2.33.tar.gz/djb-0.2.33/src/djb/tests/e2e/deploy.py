"""End-to-end tests for djb deploy CLI commands.

These tests exercise the deploy commands while mocking Heroku CLI
to avoid side effects.

Commands tested:
- djb deploy heroku
- djb deploy heroku revert
- djb deploy heroku setup

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click import ClickException

from djb.cli.deploy import _get_app_or_fail
from djb.cli.djb import djb_cli

from . import add_initial_commit, create_pyproject_toml, init_git_repo


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def deploy_project(tmp_path: Path) -> Path:
    """Create a project with git repo set up for deployment tests.

    Creates:
    - pyproject.toml
    - manage.py
    - .git initialized with heroku remote
    - Multiple commits for revert testing
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(project_dir, name="myproject")

    # Create manage.py (Django entrypoint)
    manage_py = project_dir / "manage.py"
    manage_py.write_text('#!/usr/bin/env python\nprint("manage.py")\n')

    init_git_repo(project_dir, user_email="test@example.com", user_name="Test User")
    add_initial_commit(project_dir)

    # Add heroku remote
    subprocess.run(
        [
            "git",
            "-C",
            str(project_dir),
            "remote",
            "add",
            "heroku",
            "https://git.heroku.com/myproject.git",
        ],
        capture_output=True,
    )

    # Add another commit for revert testing
    readme = project_dir / "README.md"
    readme.write_text("# My Project\n")
    subprocess.run(["git", "-C", str(project_dir), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(project_dir), "commit", "-m", "Add README"],
        capture_output=True,
    )

    return project_dir


@pytest.fixture
def mock_heroku_success():
    """Mock Heroku CLI to return success for all commands.

    Returns a side_effect function that mocks heroku commands but
    preserves the original subprocess.run for git and other commands.
    """
    # Store reference to real subprocess.run before patching
    real_run = subprocess.run

    def run_side_effect(cmd, *args, **kwargs):
        cmd_list = cmd if isinstance(cmd, list) else [cmd]
        cmd_str = " ".join(cmd_list)

        if "heroku" in cmd_str:
            # Mock various Heroku commands
            if "auth:whoami" in cmd_str:
                result = Mock(returncode=0, stdout="test@example.com\n", stderr="")
            elif "apps:info" in cmd_str:
                result = Mock(returncode=0, stdout="=== myproject\nDynos: 0\n", stderr="")
            elif "config:set" in cmd_str:
                result = Mock(returncode=0, stdout="", stderr="")
            elif "config:get" in cmd_str:
                result = Mock(returncode=0, stdout="False\n", stderr="")
            elif "buildpacks" in cmd_str and "--app" in cmd_str:
                result = Mock(returncode=0, stdout="heroku/python\n", stderr="")
            elif "buildpacks:clear" in cmd_str:
                result = Mock(returncode=0, stdout="", stderr="")
            elif "buildpacks:add" in cmd_str:
                result = Mock(returncode=0, stdout="", stderr="")
            elif "addons" in cmd_str:
                result = Mock(
                    returncode=0, stdout="heroku-postgresql (postgresql-solid-12345)\n", stderr=""
                )
            elif "run" in cmd_str:
                result = Mock(returncode=0, stdout="", stderr="")
            else:
                result = Mock(returncode=0, stdout="", stderr="")
            return result
        elif "git" in cmd_str and "push" in cmd_str and "heroku" in cmd_str:
            # Mock git push to heroku
            return Mock(returncode=0, stdout="", stderr="Everything up-to-date")
        else:
            # Run real subprocess for non-Heroku commands
            return real_run(cmd, *args, **kwargs)

    return run_side_effect


class TestGetAppOrFail:
    """E2E tests for _get_app_or_fail helper."""

    def test_returns_explicit_app(self):
        """Test that explicit app is returned."""
        result = _get_app_or_fail("myapp", None)
        assert result == "myapp"

    def test_returns_project_name_from_config(self):
        """Test that project_name from config is used as fallback."""
        mock_config = Mock()
        mock_config.project_name = "myproject"
        result = _get_app_or_fail(None, mock_config)
        assert result == "myproject"

    def test_raises_without_app_or_config(self):
        """Test that error is raised when no app name can be determined."""
        with pytest.raises(ClickException) as exc_info:
            _get_app_or_fail(None, None)
        assert "No app name provided" in str(exc_info.value)


class TestDeployHerokuSetup:
    """E2E tests for djb deploy heroku setup command."""

    def test_setup_configures_app(
        self,
        runner,
        deploy_project: Path,
        mock_heroku_success,
    ):
        """Test that setup configures buildpacks, config vars, and remote."""
        env = {
            "DJB_PROJECT_DIR": str(deploy_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_heroku_success):
                result = runner.invoke(
                    djb_cli,
                    [
                        "deploy",
                        "heroku",
                        "--app",
                        "myproject",
                        "setup",
                        "-y",
                    ],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "setup complete" in result.output.lower()

    def test_setup_with_skip_flags(
        self,
        runner,
        deploy_project: Path,
        mock_heroku_success,
    ):
        """Test that setup respects skip flags."""
        env = {
            "DJB_PROJECT_DIR": str(deploy_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_heroku_success):
                result = runner.invoke(
                    djb_cli,
                    [
                        "deploy",
                        "heroku",
                        "--app",
                        "myproject",
                        "setup",
                        "--skip-buildpacks",
                        "--skip-postgres",
                        "--skip-remote",
                        "-y",
                    ],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should complete setup (skipping doesn't mean no output about those sections)
        assert "setup complete" in result.output.lower()


class TestDeployHeroku:
    """E2E tests for djb deploy heroku command."""

    def test_deploy_requires_production_mode_warning(
        self,
        runner,
        deploy_project: Path,
        mock_heroku_success,
    ):
        """Test that deploy warns when not in production mode."""
        env = {
            "DJB_PROJECT_DIR": str(deploy_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_heroku_success):
                # Without -y, it should prompt about non-production mode
                result = runner.invoke(
                    djb_cli,
                    [
                        "deploy",
                        "heroku",
                        "--app",
                        "myproject",
                        "--skip-secrets",
                    ],
                    input="n\n",  # Decline the prompt
                )

        # Should warn about mode
        assert "mode" in result.output.lower()

    def test_deploy_with_skip_options(
        self,
        runner,
        deploy_project: Path,
        mock_heroku_success,
    ):
        """Test that deploy works with skip options."""

        env = {
            "DJB_PROJECT_DIR": str(deploy_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
            "DJB_HOSTNAME": "myproject.com",
        }

        # Mock run_streaming to simulate successful git push
        def mock_run_streaming(cmd, *args, **kwargs):
            return 0, "Everything up-to-date"

        # Change to project directory so git commands work
        old_cwd = os.getcwd()
        try:
            os.chdir(str(deploy_project))
            with patch.dict(os.environ, env):
                with patch("subprocess.run", side_effect=mock_heroku_success):
                    with patch("djb.cli.deploy.run_streaming", side_effect=mock_run_streaming):
                        result = runner.invoke(
                            djb_cli,
                            [
                                "--mode",
                                "production",
                                "deploy",
                                "heroku",
                                "--app",
                                "myproject",
                                "--skip-secrets",
                                "--skip-migrate",
                                "-y",
                            ],
                        )
        finally:
            os.chdir(old_cwd)

        # Should succeed or show "up-to-date" message
        output_lower = result.output.lower()
        assert (
            result.exit_code == 0 or "up-to-date" in output_lower
        ), f"Command failed: {result.output}"


class TestDeployHerokuRevert:
    """E2E tests for djb deploy heroku revert command."""

    def test_revert_prompts_for_confirmation(
        self,
        runner,
        deploy_project: Path,
        mock_heroku_success,
    ):
        """Test that revert prompts for confirmation."""

        env = {
            "DJB_PROJECT_DIR": str(deploy_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        # Change to project directory so git commands work
        old_cwd = os.getcwd()
        try:
            os.chdir(str(deploy_project))
            with patch.dict(os.environ, env):
                with patch("subprocess.run", side_effect=mock_heroku_success):
                    result = runner.invoke(
                        djb_cli,
                        [
                            "deploy",
                            "heroku",
                            "--app",
                            "myproject",
                            "revert",
                        ],
                        input="n\n",  # Decline the prompt
                    )
        finally:
            os.chdir(old_cwd)

        # Should prompt for confirmation and show we're reverting
        # (the confirmation prompt or cancellation message should appear)
        output_lower = result.output.lower()
        assert "revert" in output_lower or "previous" in output_lower or "continue" in output_lower

    def test_revert_to_specific_commit(
        self,
        runner,
        deploy_project: Path,
        mock_heroku_success,
    ):
        """Test reverting to a specific commit."""

        env = {
            "DJB_PROJECT_DIR": str(deploy_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        # Get the first commit hash
        commit_result = subprocess.run(
            ["git", "-C", str(deploy_project), "rev-parse", "HEAD~1"],
            capture_output=True,
            text=True,
        )
        first_commit = commit_result.stdout.strip()[:7]

        # Change to project directory so git commands work
        old_cwd = os.getcwd()
        try:
            os.chdir(str(deploy_project))
            with patch.dict(os.environ, env):
                with patch("subprocess.run", side_effect=mock_heroku_success):
                    result = runner.invoke(
                        djb_cli,
                        [
                            "deploy",
                            "heroku",
                            "--app",
                            "myproject",
                            "revert",
                            first_commit,
                        ],
                        input="y\n",  # Confirm the revert
                    )
        finally:
            os.chdir(old_cwd)

        # Should show the commit being reverted to or confirm the revert
        output_lower = result.output.lower()
        assert (
            first_commit in result.output or "revert" in output_lower or "continue" in output_lower
        )
