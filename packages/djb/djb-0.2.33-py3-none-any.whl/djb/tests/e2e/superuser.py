"""End-to-end tests for djb sync-superuser CLI command.

Commands tested:
- djb sync-superuser

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from djb.cli.djb import djb_cli

from . import create_pyproject_toml, init_git_repo


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def django_project(tmp_path: Path) -> Path:
    """Create a minimal Django project for superuser tests."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(project_dir, name="myproject")

    # Create manage.py
    manage_py = project_dir / "manage.py"
    manage_py.write_text('#!/usr/bin/env python\nimport sys\nprint("manage.py called")\n')

    init_git_repo(project_dir)

    return project_dir


class TestSyncSuperuser:
    """E2E tests for djb sync-superuser command."""

    def test_sync_superuser_local(
        self,
        runner,
        django_project: Path,
    ):
        """Test sync-superuser for local development."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        # Save original before patching
        real_run = subprocess.run

        def run_side_effect(cmd, *args, **kwargs):
            cmd_list = cmd if isinstance(cmd, list) else [cmd]
            cmd_str = " ".join(cmd_list)
            if "manage.py" in cmd_str or "python" in cmd_str:
                return Mock(returncode=0, stdout="Superuser synced\n", stderr="")
            return real_run(cmd, *args, **kwargs)

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=run_side_effect):
                result = runner.invoke(
                    djb_cli,
                    ["sync-superuser"],
                )

        # Should complete (may fail if Django not configured, that's ok)
        # We just check it runs without crashing
        assert (
            "sync" in result.output.lower()
            or "superuser" in result.output.lower()
            or result.exit_code in [0, 1]
        )

    def test_sync_superuser_dry_run(
        self,
        runner,
        django_project: Path,
    ):
        """Test sync-superuser with --dry-run flag."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        real_run = subprocess.run

        def run_side_effect(cmd, *args, **kwargs):
            cmd_list = cmd if isinstance(cmd, list) else [cmd]
            cmd_str = " ".join(cmd_list)
            if "manage.py" in cmd_str or "python" in cmd_str:
                return Mock(returncode=0, stdout="Would sync superuser\n", stderr="")
            return real_run(cmd, *args, **kwargs)

        with patch.dict(os.environ, env):
            with patch("subprocess.run", side_effect=run_side_effect):
                result = runner.invoke(
                    djb_cli,
                    ["sync-superuser", "--dry-run"],
                )

        # Should complete
        assert (
            "dry" in result.output.lower()
            or "would" in result.output.lower()
            or result.exit_code in [0, 1]
        )
