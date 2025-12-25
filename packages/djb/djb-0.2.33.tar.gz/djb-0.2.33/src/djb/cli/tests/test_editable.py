"""Tests for djb editable-djb module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from djb.cli.djb import djb_cli
from djb.cli.editable import (
    DJB_DEFAULT_DIR,
    DJB_REPO,
    PRE_COMMIT_HOOK_CONTENT,
    _get_djb_source_config,
    _get_workspace_members,
    _install_pre_commit_hook,
    _remove_djb_source_entry,
    _remove_djb_workspace_member,
    clone_djb_repo,
    find_djb_dir,
    get_djb_source_path,
    get_djb_version_specifier,
    get_installed_djb_version,
    install_editable_djb,
    is_djb_editable,
    is_djb_package_dir,
    show_status,
    uninstall_editable_djb,
)

from . import make_editable_pyproject

# Common mock return value for version display
MOCK_VERSION_OUTPUT = "Name: djb\nVersion: 0.2.5\nLocation: /path/to/site-packages"


@pytest.fixture
def mock_run_cmd():
    """Mock run_cmd to avoid actual command execution."""
    with patch("djb.cli.editable.run_cmd") as mock:
        mock.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock


@pytest.fixture
def editable_pyproject(tmp_path):
    """Create a pyproject.toml with djb in editable mode."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(make_editable_pyproject("djb"))
    return pyproject


class TestGetDjbVersionSpecifier:
    """Tests for get_djb_version_specifier function."""

    def test_returns_version_specifier(self, tmp_path):
        """Test returns version specifier when present."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    "django>=6.0.0",
    "djb>=0.2.6",
]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result == ">=0.2.6"

    def test_returns_none_when_no_djb(self, tmp_path):
        """Test returns None when djb not in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = ["django>=6.0.0"]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result is None

    def test_returns_none_when_pyproject_missing(self, tmp_path):
        """Test returns None when pyproject.toml doesn't exist."""
        result = get_djb_version_specifier(tmp_path)
        assert result is None

    @pytest.mark.parametrize(
        "dep_string,expected",
        [
            # Various version specifiers
            ("djb>=0.2.6", ">=0.2.6"),
            ("djb==0.2.6", "==0.2.6"),
            ("djb~=0.2.6", "~=0.2.6"),
            ("djb<1.0", "<1.0"),
            ("djb<=0.2.6", "<=0.2.6"),
            ("djb>0.2.5", ">0.2.5"),
            ("djb!=0.2.3", "!=0.2.3"),
            # Compound version specifiers (packaging sorts specifiers alphabetically by operator)
            ("djb>=0.2.6,<1.0", "<1.0,>=0.2.6"),
            # Extras syntax (specifier should still be extracted)
            ("djb[dev]>=0.2.6", ">=0.2.6"),
            ("djb[dev,test]>=0.2.6,<1.0", "<1.0,>=0.2.6"),
            # Dependency without version constraint
            ("djb", None),
            # No specifier with extras
            ("djb[dev]", None),
        ],
    )
    def test_handles_various_specifiers(self, tmp_path, dep_string, expected):
        """Test handles all PEP 508 version specifiers, extras, and markers."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            f"""
[project]
name = "myproject"
dependencies = [
    "{dep_string}",
]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result == expected

    def test_does_not_match_prefix_package(self, tmp_path):
        """Test does not match djb-extras when looking for djb."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    "djb-extras>=0.2.6",
]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result is None

    def test_handles_optional_dependencies(self, tmp_path):
        """Test finds djb in optional dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = []

[project.optional-dependencies]
dev = [
    "djb>=0.2.6",
]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result == ">=0.2.6"

    def test_handles_environment_markers(self, tmp_path):
        """Test handles dependencies with PEP 508 environment markers."""
        pyproject = tmp_path / "pyproject.toml"
        # Use single quotes for TOML string since marker contains double quotes
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    'djb>=0.2.6; python_version >= "3.10"',
]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result == ">=0.2.6"

    def test_handles_extras_with_markers(self, tmp_path):
        """Test handles dependencies with extras and environment markers."""
        pyproject = tmp_path / "pyproject.toml"
        # Use single quotes for TOML string since marker contains double quotes
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    'djb[dev]>=0.2.6; sys_platform == "linux"',
]
"""
        )

        result = get_djb_version_specifier(tmp_path)
        assert result == ">=0.2.6"

    def test_returns_none_for_invalid_toml(self, tmp_path):
        """Test returns None for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        result = get_djb_version_specifier(tmp_path)
        assert result is None


class TestFindDjbDir:
    """Tests for find_djb_dir function."""

    def test_finds_djb_in_subdirectory(self, tmp_path):
        """Test finding djb/ subdirectory with pyproject.toml."""
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        (djb_dir / "pyproject.toml").write_text('[project]\nname = "djb"')

        result = find_djb_dir(tmp_path)
        assert result == djb_dir

    def test_finds_djb_when_inside_djb_directory(self, tmp_path):
        """Test finding djb when cwd is inside djb directory."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "djb"\nversion = "0.1.0"')

        result = find_djb_dir(tmp_path)
        assert result == tmp_path

    def test_returns_none_when_not_found(self, tmp_path):
        """Test returns None when djb directory not found."""
        result = find_djb_dir(tmp_path)
        assert result is None

    def test_returns_none_for_non_djb_pyproject(self, tmp_path):
        """Test returns None when pyproject.toml exists but is not djb."""
        (tmp_path / "pyproject.toml").write_text('name = "other-project"')

        result = find_djb_dir(tmp_path)
        assert result is None

    def test_uses_cwd_when_repo_root_is_none(self, tmp_path):
        """Test uses current working directory when repo_root is None."""
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        (djb_dir / "pyproject.toml").write_text('name = "djb"')

        with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
            result = find_djb_dir(None)
            assert result == djb_dir


class TestIsDjbEditable:
    """Tests for is_djb_editable function."""

    def test_returns_true_when_editable(self, tmp_path, editable_pyproject):
        """Test returns True when djb is in uv.sources."""
        result = is_djb_editable(tmp_path)
        assert result is True

    def test_returns_false_when_not_editable(self, tmp_path):
        """Test returns False when djb is not in uv.sources."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[project.dependencies]
djb = "^0.1.0"
"""
        )

        result = is_djb_editable(tmp_path)
        assert result is False

    def test_returns_false_when_pyproject_missing(self, tmp_path):
        """Test returns False when pyproject.toml doesn't exist."""
        result = is_djb_editable(tmp_path)
        assert result is False

    def test_returns_false_when_sources_exists_but_no_djb(self, tmp_path):
        """Test returns False when uv.sources exists but djb not in it."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.sources]
other-package = { path = "../other" }
"""
        )

        result = is_djb_editable(tmp_path)
        assert result is False


class TestUninstallEditableDjb:
    """Tests for uninstall_editable_djb function."""

    def test_successful_uninstall(self, tmp_path, mock_run_cmd):
        """Test successful uninstall and reinstall from PyPI."""
        # Mock returns version info for the uv pip show call
        mock_run_cmd.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")

        result = uninstall_editable_djb(tmp_path)

        assert result is True
        # Calls: uv remove djb, uv add djb, uv pip show djb (for version display)
        assert mock_run_cmd.call_count == 3

        # First call: uv remove djb
        first_call = mock_run_cmd.call_args_list[0]
        assert first_call[0][0] == ["uv", "remove", "djb"]

        # Second call: uv add --refresh djb
        second_call = mock_run_cmd.call_args_list[1]
        assert second_call[0][0] == ["uv", "add", "--refresh", "djb"]

    def test_failure_on_remove(self, tmp_path, mock_run_cmd):
        """Test returns False when uv remove fails."""
        mock_run_cmd.return_value = Mock(returncode=1, stderr="error")

        result = uninstall_editable_djb(tmp_path)

        assert result is False
        assert mock_run_cmd.call_count == 1

    def test_failure_on_add(self, tmp_path, mock_run_cmd):
        """Test returns False when uv add fails after successful remove."""

        def side_effect(cmd, *args, **kwargs):
            if cmd == ["uv", "remove", "djb"]:
                return Mock(returncode=0)
            return Mock(returncode=1, stderr="error")

        mock_run_cmd.side_effect = side_effect

        result = uninstall_editable_djb(tmp_path)

        assert result is False
        assert mock_run_cmd.call_count == 2

    def test_quiet_mode_suppresses_output(self, tmp_path, mock_run_cmd, capsys):
        """Test quiet=True suppresses click.echo output."""
        uninstall_editable_djb(tmp_path, quiet=True)

        captured = capsys.readouterr()
        assert "Removing" not in captured.out
        assert "Re-adding" not in captured.out


class TestCloneDjbRepo:
    """Tests for clone_djb_repo function."""

    def test_successful_clone(self, tmp_path, mock_run_cmd):
        """Test successful git clone."""
        mock_run_cmd.return_value = Mock(returncode=0, stdout="", stderr="")
        target_dir = tmp_path / "djb"

        result = clone_djb_repo(target_dir)

        assert result is True
        mock_run_cmd.assert_called_once()
        call_args = mock_run_cmd.call_args[0][0]
        assert call_args == ["git", "clone", DJB_REPO, str(target_dir)]

    def test_clone_with_custom_repo(self, tmp_path, mock_run_cmd):
        """Test clone with custom repository URL."""
        mock_run_cmd.return_value = Mock(returncode=0, stdout="", stderr="")
        target_dir = tmp_path / "djb"
        custom_repo = "git@github.com:other/djb.git"

        result = clone_djb_repo(target_dir, djb_repo=custom_repo)

        assert result is True
        call_args = mock_run_cmd.call_args[0][0]
        assert call_args == ["git", "clone", custom_repo, str(target_dir)]

    def test_clone_failure(self, tmp_path, mock_run_cmd):
        """Test returns False when git clone fails."""
        mock_run_cmd.return_value = Mock(returncode=1, stderr="fatal: repository not found")
        target_dir = tmp_path / "djb"

        result = clone_djb_repo(target_dir)

        assert result is False

    def test_quiet_mode(self, tmp_path, mock_run_cmd, capsys):
        """Test quiet mode suppresses output."""
        mock_run_cmd.return_value = Mock(returncode=0, stdout="", stderr="")
        target_dir = tmp_path / "djb"

        clone_djb_repo(target_dir, quiet=True)

        captured = capsys.readouterr()
        assert "Cloning" not in captured.out


class TestInstallEditableDjb:
    """Tests for install_editable_djb function."""

    def test_successful_install(self, tmp_path, djb_project, mock_run_cmd):
        """Test successful editable install."""
        mock_run_cmd.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")

        result = install_editable_djb(tmp_path)

        assert result is True
        # Calls: uv add --editable, uv pip show djb (for version display)
        assert mock_run_cmd.call_count == 2
        first_call = mock_run_cmd.call_args_list[0]
        assert first_call[0][0] == ["uv", "add", "--editable", str(djb_project)]

    def test_clones_when_djb_not_found(self, tmp_path, mock_run_cmd):
        """Test clones djb repo when directory not found."""
        mock_run_cmd.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")

        result = install_editable_djb(tmp_path)

        assert result is True
        # Calls: git clone, uv add --editable, uv pip show djb
        assert mock_run_cmd.call_count == 3
        # First call should be git clone
        first_call = mock_run_cmd.call_args_list[0]
        assert first_call[0][0][0:2] == ["git", "clone"]
        assert DJB_REPO in first_call[0][0]

    def test_clone_failure_returns_false(self, tmp_path, mock_run_cmd):
        """Test returns False when git clone fails."""
        mock_run_cmd.return_value = Mock(returncode=1, stderr="clone failed")

        result = install_editable_djb(tmp_path)

        assert result is False
        # Only git clone should have been called
        assert mock_run_cmd.call_count == 1

    def test_custom_repo_and_dir(self, tmp_path, mock_run_cmd):
        """Test clone with custom repo and directory."""
        mock_run_cmd.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")
        custom_repo = "git@github.com:custom/djb.git"
        custom_dir = "packages/djb"

        result = install_editable_djb(tmp_path, djb_repo=custom_repo, djb_dir=custom_dir)

        assert result is True
        # First call should be git clone with custom repo and dir
        first_call = mock_run_cmd.call_args_list[0]
        assert first_call[0][0] == ["git", "clone", custom_repo, str(tmp_path / custom_dir)]

    def test_failure_on_uv_add(self, tmp_path, djb_project, mock_run_cmd):
        """Test returns False when uv add --editable fails."""
        mock_run_cmd.return_value = Mock(returncode=1, stderr="error")

        result = install_editable_djb(tmp_path)

        assert result is False

    def test_quiet_mode_suppresses_output(self, tmp_path, djb_project, mock_run_cmd, capsys):
        """Test quiet=True suppresses click.echo output."""
        install_editable_djb(tmp_path, quiet=True)

        captured = capsys.readouterr()
        assert "Installing" not in captured.out


class TestEditableDjbCommand:
    """Tests for editable-djb CLI command."""

    def test_help(self, runner):
        """Test that editable-djb --help works."""
        result = runner.invoke(djb_cli, ["editable-djb", "--help"])
        assert result.exit_code == 0
        assert "Install or uninstall djb in editable mode" in result.output
        assert "--uninstall" in result.output
        assert "--djb-repo" in result.output
        assert "--djb-dir" in result.output

    def test_install_success(self, runner, tmp_path, djb_project):
        """Test successful install via CLI."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb"])

        assert result.exit_code == 0
        assert "editable mode" in result.output

    def test_install_clones_when_not_found(self, runner, tmp_path):
        """Test install clones djb repo when directory not found."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb"])

        assert result.exit_code == 0
        # Check that git clone was called
        calls = [call[0][0] for call in mock_run.call_args_list]
        assert any(cmd[0:2] == ["git", "clone"] for cmd in calls)

    def test_install_failure_on_clone(self, runner, tmp_path):
        """Test install failure when clone fails."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="clone failed")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb"])

        assert result.exit_code == 1
        assert "Failed to install" in result.output

    def test_custom_repo_option(self, runner, tmp_path):
        """Test --djb-repo option."""
        custom_repo = "git@github.com:custom/djb.git"
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb", "--djb-repo", custom_repo])

        assert result.exit_code == 0
        # Check that git clone was called with custom repo
        first_call = mock_run.call_args_list[0]
        assert custom_repo in first_call[0][0]

    def test_custom_dir_option(self, runner, tmp_path):
        """Test --djb-dir option."""
        custom_dir = "packages/djb"
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb", "--djb-dir", custom_dir])

        assert result.exit_code == 0
        # Check that git clone was called with custom dir
        first_call = mock_run.call_args_list[0]
        assert str(tmp_path / custom_dir) in first_call[0][0]

    def test_uninstall_success(self, runner, tmp_path, editable_pyproject):
        """Test successful uninstall via CLI."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Version: 0.2.5", stderr="")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb", "--uninstall"])

        assert result.exit_code == 0
        assert "PyPI" in result.output

    def test_uninstall_failure(self, runner, tmp_path, editable_pyproject):
        """Test uninstall failure via CLI."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="error")
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb", "--uninstall"])

        assert result.exit_code == 1
        assert "Failed to uninstall" in result.output or "Failed to remove" in result.output


class TestGetDjbSourcePath:
    """Tests for get_djb_source_path function."""

    def test_returns_path_when_editable(self, tmp_path, editable_pyproject, djb_project):
        """Test returns path when djb is in editable mode."""
        # djb_project fixture creates tmp_path/djb/ with valid pyproject.toml
        result = get_djb_source_path(tmp_path)
        assert result == "djb"

    def test_returns_none_when_not_editable(self, tmp_path):
        """Test returns None when djb is not in editable mode."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
"""
        )

        result = get_djb_source_path(tmp_path)
        assert result is None

    def test_returns_none_when_pyproject_missing(self, tmp_path):
        """Test returns None when pyproject.toml doesn't exist."""
        result = get_djb_source_path(tmp_path)
        assert result is None


class TestGetInstalledDjbVersion:
    """Tests for get_installed_djb_version function."""

    def test_returns_version_when_installed(self, tmp_path):
        """Test returns version when djb is installed."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Name: djb\nVersion: 0.2.5\nLocation: /path/to/site-packages",
            )
            result = get_installed_djb_version(tmp_path)

        assert result == "0.2.5"

    def test_returns_none_when_not_installed(self, tmp_path):
        """Test returns None when djb is not installed."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="not found")
            result = get_installed_djb_version(tmp_path)

        assert result is None


class TestShowStatus:
    """Tests for show_status function."""

    def test_shows_editable_status(self, tmp_path, editable_pyproject, capsys):
        """Test shows editable mode status."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=MOCK_VERSION_OUTPUT)
            show_status(tmp_path)

        captured = capsys.readouterr()
        assert "0.2.5" in captured.out
        assert "editable" in captured.out.lower()

    def test_shows_pypi_status(self, tmp_path, capsys):
        """Test shows PyPI mode status."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n')

        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=MOCK_VERSION_OUTPUT)
            show_status(tmp_path)

        captured = capsys.readouterr()
        assert "0.2.5" in captured.out
        assert "PyPI" in captured.out

    def test_shows_not_installed(self, tmp_path, capsys):
        """Test shows not installed when djb is missing."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="")
            show_status(tmp_path)

        captured = capsys.readouterr()
        assert "Not installed" in captured.out


class TestEditableDjbStatusCommand:
    """Tests for editable-djb --status CLI command."""

    def test_status_flag(self, runner, tmp_path, editable_pyproject):
        """Test that --status shows current status."""
        with patch("djb.cli.editable.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=MOCK_VERSION_OUTPUT)
            with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
                result = runner.invoke(djb_cli, ["editable-djb", "--status"])

        assert result.exit_code == 0
        assert "status" in result.output.lower() or "editable" in result.output.lower()

    def test_already_editable_message(self, runner, tmp_path, editable_pyproject):
        """Test message when already in editable mode."""
        with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
            result = runner.invoke(djb_cli, ["editable-djb"])

        assert result.exit_code == 0
        assert "already" in result.output.lower()

    def test_not_editable_uninstall_message(self, runner, tmp_path):
        """Test message when uninstalling but not in editable mode."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n')

        with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
            result = runner.invoke(djb_cli, ["editable-djb", "--uninstall"])

        assert result.exit_code == 0
        assert "not" in result.output.lower()


class TestGetDjbSourceConfig:
    """Tests for _get_djb_source_config function."""

    def test_returns_config_when_present(self, tmp_path):
        """Test returns djb config dict when [tool.uv.sources.djb] is present."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.sources]
djb = { workspace = true, editable = true }
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result == {"workspace": True, "editable": True}

    def test_returns_none_when_no_djb_source(self, tmp_path):
        """Test returns None when [tool.uv.sources] has no djb entry."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.sources]
other-package = { path = "../other" }
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result is None

    def test_returns_none_when_no_sources_section(self, tmp_path):
        """Test returns None when [tool.uv.sources] section doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv]
dev-dependencies = ["pytest"]
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result is None

    def test_returns_none_when_no_uv_section(self, tmp_path):
        """Test returns None when [tool.uv] section doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.pytest]
testpaths = ["tests"]
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result is None

    def test_returns_none_when_no_tool_section(self, tmp_path):
        """Test returns None when [tool] section doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result is None

    def test_returns_none_for_missing_file(self, tmp_path):
        """Test returns None when pyproject.toml doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        result = _get_djb_source_config(pyproject)
        assert result is None

    def test_returns_none_for_invalid_toml(self, tmp_path):
        """Test returns None for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        result = _get_djb_source_config(pyproject)
        assert result is None

    def test_handles_path_based_config(self, tmp_path):
        """Test handles djb config with path instead of workspace."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.sources]
djb = { path = "../djb", editable = true }
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result == {"path": "../djb", "editable": True}

    def test_handles_empty_djb_config(self, tmp_path):
        """Test handles empty djb config dict."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.sources]
djb = {}
"""
        )

        result = _get_djb_source_config(pyproject)
        assert result == {}


class TestGetWorkspaceMembers:
    """Tests for _get_workspace_members function."""

    def test_returns_members_when_present(self, tmp_path):
        """Test returns workspace members list when configured."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.workspace]
members = ["djb", "packages/other"]
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == ["djb", "packages/other"]

    def test_returns_empty_list_when_no_members(self, tmp_path):
        """Test returns empty list when workspace has no members key."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.workspace]
exclude = ["examples/*"]
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == []

    def test_returns_empty_list_when_no_workspace_section(self, tmp_path):
        """Test returns empty list when [tool.uv.workspace] doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv]
dev-dependencies = ["pytest"]
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == []

    def test_returns_empty_list_when_no_uv_section(self, tmp_path):
        """Test returns empty list when [tool.uv] section doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.pytest]
testpaths = ["tests"]
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == []

    def test_returns_empty_list_when_no_tool_section(self, tmp_path):
        """Test returns empty list when [tool] section doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == []

    def test_returns_empty_list_for_missing_file(self, tmp_path):
        """Test returns empty list when pyproject.toml doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        result = _get_workspace_members(pyproject)
        assert result == []

    def test_returns_empty_list_for_invalid_toml(self, tmp_path):
        """Test returns empty list for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        result = _get_workspace_members(pyproject)
        assert result == []

    def test_handles_single_member(self, tmp_path):
        """Test handles single workspace member."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.workspace]
members = ["djb"]
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == ["djb"]

    def test_handles_empty_members_list(self, tmp_path):
        """Test handles empty members list."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.workspace]
members = []
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == []

    def test_handles_glob_patterns_in_members(self, tmp_path):
        """Test handles glob patterns in members list."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"

[tool.uv.workspace]
members = ["packages/*", "djb"]
"""
        )

        result = _get_workspace_members(pyproject)
        assert result == ["packages/*", "djb"]


class TestIsDjbPackageDir:
    """Tests for is_djb_package_dir function."""

    def test_returns_true_for_valid_djb_package(self, tmp_path):
        """Test returns True when pyproject.toml has name = "djb"."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "djb"')

        result = is_djb_package_dir(tmp_path)
        assert result is True

    def test_returns_false_for_different_package_name(self, tmp_path):
        """Test returns False when pyproject.toml has a different package name."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "other-package"')

        result = is_djb_package_dir(tmp_path)
        assert result is False

    def test_returns_false_when_pyproject_missing(self, tmp_path):
        """Test returns False when pyproject.toml doesn't exist."""
        result = is_djb_package_dir(tmp_path)
        assert result is False

    def test_returns_false_for_invalid_toml(self, tmp_path):
        """Test returns False for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        result = is_djb_package_dir(tmp_path)
        assert result is False

    def test_returns_false_when_project_section_missing(self, tmp_path):
        """Test returns False when [project] section doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.pytest]\ntestpaths = ["tests"]')

        result = is_djb_package_dir(tmp_path)
        assert result is False

    def test_returns_false_when_name_missing(self, tmp_path):
        """Test returns False when [project] exists but name key is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"')

        result = is_djb_package_dir(tmp_path)
        assert result is False

    def test_returns_false_for_empty_file(self, tmp_path):
        """Test returns False for empty pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        result = is_djb_package_dir(tmp_path)
        assert result is False

    def test_handles_full_pyproject_structure(self, tmp_path):
        """Test with a realistic pyproject.toml structure."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "djb"
version = "0.2.30"
description = "Django Backend development tools"

[project.dependencies]
click = ">=8.0"

[tool.uv]
dev-dependencies = ["pytest", "ruff"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
        )

        result = is_djb_package_dir(tmp_path)
        assert result is True


class TestRemoveDjbWorkspaceMember:
    """Tests for _remove_djb_workspace_member function."""

    def test_removes_workspace_section_with_only_djb(self, tmp_path):
        """Test removes entire [tool.uv.workspace] section when djb is only member."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.workspace]
members = [
    "djb",
]

[tool.uv.sources]
djb = { workspace = true, editable = true }
"""
        )

        result = _remove_djb_workspace_member(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "[tool.uv.workspace]" not in content
        assert '"djb"' not in content
        # Other content should remain
        assert "[project]" in content
        assert "[tool.uv.sources]" in content

    def test_handles_compact_format(self, tmp_path):
        """Test handles compact single-line workspace format."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.workspace]
members = ["djb"]

[tool.uv.sources]
djb = { workspace = true, editable = true }
"""
        )

        result = _remove_djb_workspace_member(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "[tool.uv.workspace]" not in content

    def test_returns_true_when_no_workspace_section(self, tmp_path):
        """Test returns True (no-op) when no workspace section exists."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"
"""
        )

        result = _remove_djb_workspace_member(pyproject)

        assert result is True
        # File unchanged
        assert "[project]" in pyproject.read_text()

    def test_returns_true_when_no_djb_in_workspace(self, tmp_path):
        """Test returns True (no-op) when djb not in workspace members."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.workspace]
members = ["other-package"]
"""
        )

        result = _remove_djb_workspace_member(pyproject)

        assert result is True
        # File unchanged
        content = pyproject.read_text()
        assert "[tool.uv.workspace]" in content
        assert '"other-package"' in content

    def test_returns_true_when_file_missing(self, tmp_path):
        """Test returns True when pyproject.toml doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"

        result = _remove_djb_workspace_member(pyproject)

        assert result is True

    def test_warns_on_complex_format(self, tmp_path, capsys):
        """Test warns when format is too complex for regex (multiple members)."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.workspace]
members = ["djb", "other-package"]
"""
        )

        result = _remove_djb_workspace_member(pyproject, quiet=False)

        assert result is True  # Still returns True (non-fatal)
        captured = capsys.readouterr()
        assert "manually" in captured.out.lower() or "manually" in captured.err.lower()


class TestInstallPreCommitHook:
    """Tests for _install_pre_commit_hook function."""

    def test_installs_hook_in_git_repo(self, tmp_path):
        """Test installs hook when .git directory exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = _install_pre_commit_hook(tmp_path, quiet=True)

        assert result is True
        hook_path = git_dir / "hooks" / "pre-commit"
        assert hook_path.exists()
        assert hook_path.read_text() == PRE_COMMIT_HOOK_CONTENT
        # Check executable
        assert hook_path.stat().st_mode & 0o111  # Has execute bits

    def test_creates_hooks_dir_if_missing(self, tmp_path):
        """Test creates hooks directory if it doesn't exist."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        # Note: hooks dir doesn't exist

        result = _install_pre_commit_hook(tmp_path, quiet=True)

        assert result is True
        assert (git_dir / "hooks" / "pre-commit").exists()

    def test_updates_existing_hook(self, tmp_path):
        """Test updates hook if it already exists with different content."""
        git_dir = tmp_path / ".git"
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True)
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho 'old hook'\n")

        result = _install_pre_commit_hook(tmp_path, quiet=True)

        assert result is True
        assert hook_path.read_text() == PRE_COMMIT_HOOK_CONTENT

    def test_skips_if_already_up_to_date(self, tmp_path):
        """Test returns True without writing if content matches."""
        git_dir = tmp_path / ".git"
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True)
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(PRE_COMMIT_HOOK_CONTENT)
        original_mtime = hook_path.stat().st_mtime

        result = _install_pre_commit_hook(tmp_path, quiet=True)

        assert result is True
        # File should not have been modified
        assert hook_path.stat().st_mtime == original_mtime

    def test_returns_false_if_not_git_repo(self, tmp_path):
        """Test returns False when not in a git repo."""
        # No .git directory

        result = _install_pre_commit_hook(tmp_path, quiet=True)

        assert result is False

    def test_returns_false_if_git_is_file(self, tmp_path):
        """Test returns False when .git is a file (submodule worktree)."""
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /some/path")

        result = _install_pre_commit_hook(tmp_path, quiet=True)

        assert result is False


class TestRemoveDjbSourceEntry:
    """Tests for _remove_djb_source_entry function."""

    def test_removes_workspace_source_entry(self, tmp_path):
        """Test removes djb = { workspace = true } from sources."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.sources]
djb = { workspace = true }
"""
        )

        result = _remove_djb_source_entry(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "djb" not in content
        # Empty sources section should be removed
        assert "[tool.uv.sources]" not in content
        assert "[project]" in content

    def test_removes_editable_source_entry(self, tmp_path):
        """Test removes djb = { workspace = true, editable = true } from sources."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.sources]
djb = { workspace = true, editable = true }
"""
        )

        result = _remove_djb_source_entry(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "djb" not in content
        assert "[tool.uv.sources]" not in content

    def test_removes_path_source_entry(self, tmp_path):
        """Test removes djb = { path = "djb", editable = true } from sources."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.sources]
djb = { path = "djb", editable = true }
"""
        )

        result = _remove_djb_source_entry(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "djb" not in content
        assert "[tool.uv.sources]" not in content

    def test_preserves_other_sources(self, tmp_path):
        """Test preserves other source entries when removing djb."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.sources]
djb = { workspace = true }
other-package = { path = "other" }
"""
        )

        result = _remove_djb_source_entry(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "djb" not in content
        # Other source and section should remain
        assert "[tool.uv.sources]" in content
        assert "other-package" in content

    def test_returns_true_when_no_sources_section(self, tmp_path):
        """Test returns True (no-op) when no sources section exists."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"
"""
        )

        result = _remove_djb_source_entry(pyproject)

        assert result is True

    def test_returns_true_when_file_missing(self, tmp_path):
        """Test returns True when pyproject.toml doesn't exist."""
        pyproject = tmp_path / "pyproject.toml"

        result = _remove_djb_source_entry(pyproject)

        assert result is True

    def test_returns_true_when_no_djb_in_sources(self, tmp_path):
        """Test returns True (no-op) when djb not in sources."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """\
[project]
name = "myproject"

[tool.uv.sources]
other-package = { path = "other" }
"""
        )

        result = _remove_djb_source_entry(pyproject)

        assert result is True
        content = pyproject.read_text()
        assert "other-package" in content
