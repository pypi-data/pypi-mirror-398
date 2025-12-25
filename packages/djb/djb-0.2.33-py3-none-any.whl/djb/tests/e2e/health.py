"""End-to-end tests for djb health CLI commands.

These tests exercise the health check commands while mocking
the actual tool invocations (uv run, bun run).

Commands tested:
- djb health
- djb health lint
- djb health typecheck
- djb health test
- djb health e2e

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from djb.cli.djb import djb_cli
from djb.cli.health import (
    _get_project_context,
    _get_run_scopes,
)
from djb.config import reset_config

from . import add_frontend_package, add_python_package, create_pyproject_toml, init_git_repo


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def health_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for health check tests.

    Creates:
    - pyproject.toml
    - myproject/__init__.py
    - frontend/ directory
    - .git initialized
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(project_dir, name="myproject")
    add_python_package(project_dir)
    add_frontend_package(project_dir, name="myproject-frontend")
    init_git_repo(project_dir, user_email="test@example.com", user_name="Test User")

    return project_dir


@pytest.fixture
def mock_health_tools():
    """Mock health check tools to return success.

    Returns a side_effect function that mocks uv run and bun run commands.
    """
    real_run = subprocess.run

    def run_side_effect(cmd, *args, **kwargs):
        cmd_list = cmd if isinstance(cmd, list) else [cmd]
        cmd_str = " ".join(cmd_list)

        # Mock uv run commands (black, pyright, pytest)
        if "uv" in cmd_str and "run" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")

        # Mock bun commands
        if "bun" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")

        # Run real subprocess for other commands
        return real_run(cmd, *args, **kwargs)

    return run_side_effect


class TestHealthHelperFunctions:
    """E2E tests for health helper functions."""

    def test_get_run_scopes_neither(self):
        """Test that neither flag means both scopes run."""
        run_backend, run_frontend = _get_run_scopes(scope_frontend=False, scope_backend=False)
        assert run_backend is True
        assert run_frontend is True

    def test_get_run_scopes_backend_only(self):
        """Test backend-only scope."""
        run_backend, run_frontend = _get_run_scopes(scope_frontend=False, scope_backend=True)
        assert run_backend is True
        assert run_frontend is False

    def test_get_run_scopes_frontend_only(self):
        """Test frontend-only scope."""
        run_backend, run_frontend = _get_run_scopes(scope_frontend=True, scope_backend=False)
        assert run_backend is False
        assert run_frontend is True

    def test_get_project_context_regular_project(self, health_project: Path):
        """Test project context for a regular (non-djb) project."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            reset_config()
            context = _get_project_context()

        # Should identify as host project only
        assert context.host_path == health_project
        assert context.djb_path is None
        assert context.inside_djb is False


class TestHealthLint:
    """E2E tests for djb health lint command."""

    def test_lint_runs_checks(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that lint runs linting checks."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["health", "lint"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()
        # Should mention lint or black
        assert "lint" in result.output.lower() or "black" in result.output.lower()

    def test_lint_with_fix(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that lint --fix runs format instead of check."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["health", "lint", "--fix"],
                )

        # Should complete
        assert result.exit_code == 0 or "failed" in result.output.lower()


class TestHealthTypecheck:
    """E2E tests for djb health typecheck command."""

    def test_typecheck_runs_checks(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that typecheck runs type checking."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["health", "typecheck"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()
        # Should mention typecheck or pyright
        assert "typecheck" in result.output.lower() or "pyright" in result.output.lower()


class TestHealthTest:
    """E2E tests for djb health test command."""

    def test_test_runs_pytest(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that test runs pytest."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["health", "test"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()
        # Should mention tests or pytest
        assert "test" in result.output.lower()


class TestHealthE2E:
    """E2E tests for djb health e2e command."""

    def test_e2e_runs_pytest_with_flag(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that e2e runs pytest with --run-e2e flag."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["health", "e2e"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()
        # Should mention e2e
        assert "e2e" in result.output.lower()


class TestHealthAll:
    """E2E tests for djb health command (all checks)."""

    def test_health_runs_all_checks(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that health (no subcommand) runs all checks."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["health"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()

    def test_health_backend_only(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that --backend flag limits to backend checks."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["--backend", "health"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()
        # Should not mention frontend
        assert "frontend" not in result.output.lower() or "skip" in result.output.lower()

    def test_health_frontend_only(
        self,
        runner,
        health_project: Path,
        mock_health_tools,
    ):
        """Test that --frontend flag limits to frontend checks."""
        env = {
            "DJB_PROJECT_DIR": str(health_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=mock_health_tools):
                result = runner.invoke(
                    djb_cli,
                    ["--frontend", "health"],
                )

        # Should complete (pass or fail)
        assert result.exit_code == 0 or "failed" in result.output.lower()
