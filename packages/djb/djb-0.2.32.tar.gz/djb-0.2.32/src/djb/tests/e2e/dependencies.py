"""End-to-end tests for djb dependencies CLI command.

Commands tested:
- djb --backend dependencies
- djb --frontend dependencies
- djb dependencies --bump

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from djb.cli.djb import djb_cli

from . import create_pyproject_toml


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def deps_project(tmp_path: Path) -> Path:
    """Create a minimal project for dependencies tests."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(
        project_dir,
        name="myproject",
        extra_content='dependencies = ["django>=4.0"]',
    )

    # Create frontend directory with custom package.json (scripts needed)
    frontend_dir = project_dir / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text(
        '{"name": "myproject", "scripts": {"refresh-deps": "echo ok"}}'
    )

    return project_dir


@pytest.fixture
def mock_deps_tools():
    """Mock dependency tools (uv, bun)."""
    real_run = subprocess.run

    def run_side_effect(cmd, *args, **kwargs):
        cmd_list = cmd if isinstance(cmd, list) else [cmd]
        cmd_str = " ".join(cmd_list)

        if "uv" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")
        if "bun" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")

        return real_run(cmd, *args, **kwargs)

    return run_side_effect


class TestDependencies:
    """E2E tests for djb dependencies command."""

    def test_dependencies_requires_scope(
        self,
        runner,
        deps_project: Path,
    ):
        """Test that dependencies requires --backend or --frontend."""
        env = {
            "DJB_PROJECT_DIR": str(deps_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(djb_cli, ["dependencies"])

        # Should fail with helpful error
        assert result.exit_code != 0
        assert "backend" in result.output.lower() or "frontend" in result.output.lower()

    def test_dependencies_backend(
        self,
        runner,
        deps_project: Path,
        mock_deps_tools,
    ):
        """Test backend dependency refresh."""
        env = {
            "DJB_PROJECT_DIR": str(deps_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        def mock_streaming(cmd, *args, **kwargs):
            return 0, "", ""

        with patch.dict(os.environ, env):
            with patch("djb.cli.dependencies.run_streaming", side_effect=mock_streaming):
                result = runner.invoke(
                    djb_cli,
                    ["--backend", "dependencies"],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "backend" in result.output.lower() or "python" in result.output.lower()

    def test_dependencies_frontend(
        self,
        runner,
        deps_project: Path,
        mock_deps_tools,
    ):
        """Test frontend dependency refresh."""
        env = {
            "DJB_PROJECT_DIR": str(deps_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        def mock_streaming(cmd, *args, **kwargs):
            return 0, "", ""

        with patch.dict(os.environ, env):
            with patch("djb.cli.dependencies.run_streaming", side_effect=mock_streaming):
                result = runner.invoke(
                    djb_cli,
                    ["--frontend", "dependencies"],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "frontend" in result.output.lower()

    def test_dependencies_bump(
        self,
        runner,
        deps_project: Path,
        mock_deps_tools,
    ):
        """Test dependency bump with --bump flag."""
        env = {
            "DJB_PROJECT_DIR": str(deps_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        def mock_streaming(cmd, *args, **kwargs):
            return 0, "", ""

        with patch.dict(os.environ, env):
            with patch("djb.cli.dependencies.run_streaming", side_effect=mock_streaming):
                result = runner.invoke(
                    djb_cli,
                    ["--backend", "dependencies", "--bump"],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should mention bump
        assert "bump=yes" in result.output.lower()
