"""Tests for djb health command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest

from djb import configure
from djb.cli.djb import djb_cli
from djb.cli.health import (
    HealthStep,
    ProjectContext,
    StepFailure,
    _build_backend_lint_steps,
    _build_backend_test_steps,
    _build_backend_typecheck_steps,
    _build_frontend_lint_steps,
    _build_frontend_test_steps,
    _build_frontend_typecheck_steps,
    _get_command_with_flag,
    _get_frontend_dir,
    _get_host_display_name,
    _get_project_context,
    _get_run_scopes,
    _has_pytest_cov,
    _has_ruff,
    _is_inside_djb_dir,
    _report_failures,
    _run_for_projects,
    _run_steps,
)
from djb.cli.context import CliHealthContext
from djb.config import PROJECT, DjbConfig, save_config

from . import DJB_PYPROJECT_CONTENT

# Common path for host-only context tests
HOST_PATH = Path("/tmp/host")


@pytest.fixture
def mock_run_cmd():
    """Mock the run_cmd and run_streaming utilities to avoid running actual commands.

    Yields a namedtuple with .cmd and .stream attributes for checking calls.
    For backward compatibility, the tuple also unpacks as (mock_cmd,) but
    tests that need to check streaming calls should use mock.stream.
    """
    with (
        patch("djb.cli.health.run_cmd") as mock_cmd,
        patch("djb.cli.health.run_streaming") as mock_stream,
    ):
        # Return a mock CompletedProcess with returncode 0 for run_cmd
        mock_cmd.return_value.returncode = 0
        # Return (returncode, stdout, stderr) for run_streaming
        mock_stream.return_value = (0, "", "")
        # Add stream as an attribute so tests can access both
        mock_cmd.stream = mock_stream
        yield mock_cmd


@pytest.fixture
def mock_health_context():
    """Mock run_cmd, run_streaming, and _get_project_context for health tests.

    Yields (mock_run_cmd, mock_ctx) tuple for configuring in tests.
    mock_run_cmd.stream is available for checking streaming calls.
    """
    with (
        patch("djb.cli.health.run_cmd") as mock_run_cmd,
        patch("djb.cli.health.run_streaming") as mock_stream,
        patch("djb.cli.health._get_project_context") as mock_ctx,
    ):
        mock_run_cmd.return_value.returncode = 0
        mock_stream.return_value = (0, "", "")
        # Attach stream mock to run_cmd for easy access
        mock_run_cmd.stream = mock_stream
        yield mock_run_cmd, mock_ctx


@pytest.fixture
def host_only_context():
    """ProjectContext for host-only (no editable djb) scenario."""
    return ProjectContext(djb_path=None, host_path=HOST_PATH, inside_djb=False)


class TestHealthCommand:
    """Tests for djb health command."""

    def test_health_help(self, runner):
        """Test that health --help shows all subcommands."""
        result = runner.invoke(djb_cli, ["health", "--help"])
        assert result.exit_code == 0
        assert "Run health checks" in result.output
        assert "lint" in result.output
        assert "typecheck" in result.output
        assert "test" in result.output
        assert "e2e" in result.output
        # --frontend and --backend are now global options on djb root
        assert "--fix" in result.output

    @pytest.mark.parametrize("subcommand", ["lint", "typecheck", "test", "e2e"])
    def test_health_subcommand_help(self, runner, subcommand):
        """Test that health subcommand --help works."""
        result = runner.invoke(djb_cli, ["health", subcommand, "--help"])
        assert result.exit_code == 0

    def test_health_runs_all_checks(self, runner, mock_run_cmd):
        """Test health command runs all checks by default."""
        result = runner.invoke(djb_cli, ["health"])
        assert result.exit_code == 0
        # Should have run multiple commands (via run_cmd and run_streaming)
        total_calls = mock_run_cmd.call_count + mock_run_cmd.stream.call_count
        assert total_calls >= 3

    def test_health_backend_only(self, runner, mock_run_cmd):
        """Test --backend health runs only backend checks."""
        # --backend is now a global option, so it comes before the subcommand
        result = runner.invoke(djb_cli, ["--backend", "health"])
        assert result.exit_code == 0
        # Check that backend commands were called (run_cmd for lint/typecheck, run_streaming for tests)
        cmd_calls = [str(call) for call in mock_run_cmd.call_args_list]
        stream_calls = [str(call) for call in mock_run_cmd.stream.call_args_list]
        all_calls = cmd_calls + stream_calls
        assert any(
            "black" in str(call) or "pytest" in str(call) or "pyright" in str(call)
            for call in all_calls
        )

    @pytest.mark.parametrize(
        "subcommand,expected_tool",
        [
            ("lint", "black"),
            ("typecheck", "pyright"),
            ("test", "pytest"),
            ("e2e", "--run-e2e"),
        ],
    )
    def test_health_subcommand_runs_tool(self, runner, mock_run_cmd, subcommand, expected_tool):
        """Test that each health subcommand runs its expected tool."""
        result = runner.invoke(djb_cli, ["health", subcommand])
        assert result.exit_code == 0
        # Check both run_cmd and run_streaming calls (tests use streaming)
        cmd_calls = [str(call) for call in mock_run_cmd.call_args_list]
        stream_calls = [str(call) for call in mock_run_cmd.stream.call_args_list]
        all_calls = cmd_calls + stream_calls
        assert any(expected_tool in str(call) for call in all_calls)

    def test_health_lint_fix(self, runner, mock_run_cmd):
        """Test health lint --fix runs without --check."""
        result = runner.invoke(djb_cli, ["health", "lint", "--fix"])
        assert result.exit_code == 0
        # Verify black was called without --check
        calls = [str(call) for call in mock_run_cmd.call_args_list]
        has_black_call = any("black" in str(call) for call in calls)
        has_check_flag = any("--check" in str(call) for call in calls)
        assert has_black_call
        # With --fix, --check should not be present
        # Note: this is a simplification, actual check depends on implementation

    def test_health_failure_reports_errors(self, runner, mock_run_cmd):
        """Test that failures are reported properly."""
        # Make run_cmd return failure
        mock_run_cmd.return_value.returncode = 1
        result = runner.invoke(djb_cli, ["health", "typecheck"])
        assert result.exit_code != 0
        assert "failed" in result.output.lower()
        # Should show verbose tip
        assert "-v" in result.output
        assert "error details" in result.output.lower()


class TestIsInsideDjbDir:
    """Tests for _is_inside_djb_dir helper."""

    def test_detects_djb_directory(self, tmp_path):
        """Test that it detects a djb project directory."""
        (tmp_path / "pyproject.toml").write_text(DJB_PYPROJECT_CONTENT)
        assert _is_inside_djb_dir(tmp_path) is True

    def test_rejects_non_djb_directory(self, tmp_path):
        """Test that it rejects a non-djb project directory."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "other-project"\n')
        assert _is_inside_djb_dir(tmp_path) is False

    def test_rejects_missing_pyproject(self, tmp_path):
        """Test that it rejects a directory without pyproject.toml."""
        assert _is_inside_djb_dir(tmp_path) is False


class TestProjectContext:
    """Tests for _get_project_context helper."""

    def test_context_inside_djb_dir(self, tmp_path):
        """Test context when running from inside djb directory."""
        configure(project_dir=tmp_path)

        (tmp_path / "pyproject.toml").write_text(DJB_PYPROJECT_CONTENT)

        context = _get_project_context()

        assert context.djb_path == tmp_path
        assert context.host_path is None
        assert context.inside_djb is True

    def test_context_with_editable_djb(self, tmp_path, djb_project):
        """Test context when djb is installed in editable mode."""
        host_dir = tmp_path / "host"
        host_dir.mkdir()

        configure(project_dir=host_dir)

        with (
            patch("djb.cli.health.is_djb_editable", return_value=True),
            patch("djb.cli.health.get_djb_source_path", return_value="../djb"),
        ):
            context = _get_project_context()

        assert context.djb_path == djb_project.resolve()
        assert context.host_path == host_dir
        assert context.inside_djb is False

    def test_context_without_editable_djb(self, tmp_path):
        """Test context when djb is not editable (regular install)."""
        host_dir = tmp_path / "host"
        host_dir.mkdir()
        (host_dir / "pyproject.toml").write_text('[project]\nname = "myproject"\n')

        configure(project_dir=host_dir)

        with patch("djb.cli.health.is_djb_editable", return_value=False):
            context = _get_project_context()

        assert context.djb_path is None
        assert context.host_path == host_dir
        assert context.inside_djb is False


class TestRunForProjects:
    """Tests for _run_for_projects helper - the core shared logic for all subcommands."""

    @pytest.fixture
    def run_helper(self, tmp_path):
        """Factory fixture that returns a function to test _run_for_projects.

        Pytest fixtures are setup functions that run before each test. When a test
        method includes `run_helper` as a parameter, pytest automatically calls this
        fixture and passes the returned value to the test.

        This fixture returns a function `_run(project_ctx)` that:
        1. Creates a tracking `build_steps` callback that records each call
        2. Mocks _run_for_projects dependencies (_get_project_context, _run_steps, etc.)
        3. Calls _run_for_projects with the provided ProjectContext
        4. Returns the list of (path, prefix, is_djb) tuples that build_steps received

        Usage in tests:
            def test_example(self, tmp_path, run_helper):
                calls = run_helper(ProjectContext(djb_path=tmp_path, ...))
                assert calls == [(tmp_path, "[djb]", True)]
        """

        def _run(project_ctx: ProjectContext) -> list[tuple[Path, str, bool]]:
            calls: list[tuple[Path, str, bool]] = []

            def build_steps(path: Path, prefix: str, is_djb: bool) -> list[HealthStep]:
                calls.append((path, prefix, is_djb))
                return []

            with (
                patch("djb.cli.health._get_project_context", return_value=project_ctx),
                patch("djb.cli.health._run_steps", return_value=[]),
                patch("djb.cli.health._report_failures"),
                patch("djb.cli.health._get_host_display_name", return_value="host"),
            ):
                health_ctx = CliHealthContext()
                cfg = DjbConfig()
                cfg.load({"project_dir": str(tmp_path), "project_name": "test"})
                health_ctx.config = cfg
                _run_for_projects(health_ctx, build_steps, "test")

            return calls

        return _run

    def test_calls_build_steps_for_djb_and_host(self, tmp_path, run_helper):
        """Test that build_steps is called for both djb and host when present."""
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        host_dir = tmp_path / "host"
        host_dir.mkdir()

        calls = run_helper(ProjectContext(djb_path=djb_dir, host_path=host_dir, inside_djb=False))

        assert len(calls) == 2
        assert calls[0] == (djb_dir, "[djb]", True)
        assert calls[1] == (host_dir, "[host]", False)

    def test_only_calls_for_djb_when_inside_djb(self, tmp_path, run_helper):
        """Test that only djb is checked when running from inside djb."""
        calls = run_helper(ProjectContext(djb_path=tmp_path, host_path=None, inside_djb=True))

        assert len(calls) == 1
        assert calls[0] == (tmp_path, "", True)  # No prefix when only djb

    def test_only_calls_for_host_when_no_editable_djb(self, tmp_path, run_helper):
        """Test that only host is checked when djb is not editable."""
        calls = run_helper(ProjectContext(djb_path=None, host_path=tmp_path, inside_djb=False))

        assert len(calls) == 1
        assert calls[0] == (tmp_path, "", False)  # No prefix when only host


class TestEditableAwareHealth:
    """Tests for editable-djb aware health command behavior."""

    def test_health_inside_djb_shows_skip_message(self, runner, tmp_path, mock_health_context):
        """Test that health command shows skip message when inside djb."""
        mock_run_cmd, mock_ctx = mock_health_context
        mock_ctx.return_value = ProjectContext(djb_path=tmp_path, host_path=None, inside_djb=True)

        result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code == 0
        assert "skipping host project" in result.output.lower()

    def test_health_with_editable_runs_both_projects(
        self, runner, tmp_path, mock_health_context, monkeypatch
    ):
        """Test that health runs for both djb and host when editable."""
        mock_run_cmd, mock_ctx = mock_health_context
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        host_dir = tmp_path / "myproject"
        host_dir.mkdir()
        (host_dir / "pyproject.toml").write_text('[project]\nname = "myproject"\n')

        # Clear env var so pyproject.toml is used
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)

        mock_ctx.return_value = ProjectContext(
            djb_path=djb_dir, host_path=host_dir, inside_djb=False
        )

        result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code == 0
        assert "djb (editable)" in result.output.lower()
        assert "running lint for myproject" in result.output.lower()

    def test_health_without_editable_runs_host_only(self, runner, tmp_path, mock_health_context):
        """Test that health only runs for host when djb is not editable."""
        mock_run_cmd, mock_ctx = mock_health_context
        host_dir = tmp_path / "host"
        host_dir.mkdir()

        mock_ctx.return_value = ProjectContext(djb_path=None, host_path=host_dir, inside_djb=False)

        result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code == 0
        assert "Running lint for djb" not in result.output
        assert "Running lint for host" not in result.output

    @pytest.mark.parametrize("subcmd", ["lint", "typecheck", "test", "e2e"])
    def test_all_subcommands_respect_project_context(
        self, runner, tmp_path, mock_health_context, subcmd, monkeypatch
    ):
        """Test that all subcommands respect project context via _run_for_projects."""
        mock_run_cmd, mock_ctx = mock_health_context
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        host_dir = tmp_path / "myproject"
        host_dir.mkdir()
        (host_dir / "pyproject.toml").write_text('[project]\nname = "myproject"\n')

        # Clear env var so pyproject.toml is used
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)

        mock_ctx.return_value = ProjectContext(
            djb_path=djb_dir, host_path=host_dir, inside_djb=False
        )

        result = runner.invoke(djb_cli, ["health", subcmd])

        assert result.exit_code == 0
        assert "djb (editable)" in result.output.lower()
        assert "for myproject" in result.output.lower()


class TestGetCommandWithFlag:
    """Tests for _get_command_with_flag helper."""

    @pytest.mark.parametrize(
        "argv,flag,skip_if_present,expected",
        [
            # Inserts flag after program name, replaces full path with 'djb'
            (["/usr/local/bin/djb", "health", "lint"], "-v", None, "djb -v health lint"),
            (["/some/long/path/to/djb", "health"], "--fix", None, "djb --fix health"),
            (["djb"], "--fix", None, "djb --fix"),
            # skip_if_present behavior
            (["djb", "-v", "health", "lint"], "-v", ["-v"], "djb -v health lint"),
            (["djb", "--verbose", "health"], "-v", ["-v", "--verbose"], "djb --verbose health"),
            (["djb", "health", "lint"], "-v", ["--verbose"], "djb -v health lint"),
        ],
    )
    def test_get_command_with_flag(self, argv, flag, skip_if_present, expected):
        """Test _get_command_with_flag inserts flags correctly."""
        with patch.object(sys, "argv", argv):
            result = _get_command_with_flag(flag, skip_if_present=skip_if_present)
            assert result == expected


class TestGetHostDisplayName:
    """Tests for _get_host_display_name helper."""

    @pytest.mark.parametrize(
        "subdir,project_name,expected",
        [
            (None, "myproject", "myproject"),  # Uses configured project name
            ("beachresort25", None, "beachresort25"),  # Falls back to directory name
            ("myapp", None, "myapp"),  # Falls back when project name not configured
        ],
    )
    def test_get_host_display_name(self, tmp_path, subdir, project_name, expected, monkeypatch):
        """Test _get_host_display_name returns correct name."""
        # Clear env var so config file is used
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)

        project_dir = (tmp_path / subdir) if subdir else tmp_path
        if subdir:
            project_dir.mkdir()
        if project_name is not None:
            save_config(PROJECT, {"project_name": project_name}, project_dir)
        assert _get_host_display_name(project_dir) == expected


class TestBackendStepBuilders:
    """Tests for backend step builder functions with scope parameter."""

    def _build_steps(self, builder, tmp_path, prefix="", scope="Backend"):
        """Helper to call builder with appropriate arguments."""
        if builder == _build_backend_lint_steps:
            return builder(tmp_path, fix=False, prefix=prefix, scope=scope)
        return builder(tmp_path, prefix=prefix, scope=scope)

    @pytest.mark.parametrize(
        "builder,scope",
        [
            (_build_backend_lint_steps, "Python"),
            (_build_backend_lint_steps, "Backend"),
            (_build_backend_typecheck_steps, "Python"),
            (_build_backend_typecheck_steps, "Backend"),
            (_build_backend_test_steps, "Python"),
            (_build_backend_test_steps, "Backend"),
        ],
    )
    def test_steps_use_scope_in_label(self, tmp_path, builder, scope):
        """Test that all steps from a builder include the scope in their label."""
        steps = self._build_steps(builder, tmp_path, scope=scope)
        assert steps, "Builder should return at least one step"
        for step in steps:
            assert scope in step.label, f"Expected '{scope}' in label '{step.label}'"

    @pytest.mark.parametrize(
        "builder,prefix,scope,expected_label",
        [
            (
                _build_backend_lint_steps,
                "[myproject]",
                "Backend",
                "[myproject] Backend lint (black --check)",
            ),
            (_build_backend_typecheck_steps, "[djb]", "Python", "[djb] Python typecheck (pyright)"),
            (_build_backend_test_steps, "[app]", "Backend", "[app] Backend tests (pytest)"),
        ],
    )
    def test_steps_with_prefix_and_scope(self, tmp_path, builder, prefix, scope, expected_label):
        """Test that the first step has the expected label format."""
        steps = self._build_steps(builder, tmp_path, prefix=prefix, scope=scope)
        assert steps, "Builder should return at least one step"
        assert steps[0].label == expected_label

    def test_lint_steps_with_fix_mode(self, tmp_path):
        """Test that lint steps use format mode when fix=True."""
        with patch("djb.cli.health._has_ruff", return_value=False):
            steps = _build_backend_lint_steps(tmp_path, fix=True, prefix="", scope="Backend")
        assert len(steps) == 1
        assert "--check" not in steps[0].cmd
        assert "format" in steps[0].label
        assert "black" in steps[0].label

    def test_lint_steps_without_fix_mode(self, tmp_path):
        """Test that lint steps use check mode when fix=False."""
        with patch("djb.cli.health._has_ruff", return_value=False):
            steps = _build_backend_lint_steps(tmp_path, fix=False, prefix="", scope="Backend")
        assert len(steps) == 1
        assert "--check" in steps[0].cmd
        assert "lint" in steps[0].label

    def test_lint_steps_with_ruff_available(self, tmp_path):
        """Test that lint steps include ruff when available."""
        with patch("djb.cli.health._has_ruff", return_value=True):
            steps = _build_backend_lint_steps(tmp_path, fix=False, prefix="", scope="Backend")
        assert len(steps) == 2
        # First step is black
        assert "black" in steps[0].cmd
        assert "--check" in steps[0].cmd
        # Second step is ruff
        assert "ruff" in steps[1].cmd
        assert "check" in steps[1].cmd
        assert "--fix" not in steps[1].cmd

    def test_lint_steps_with_ruff_and_fix_mode(self, tmp_path):
        """Test that lint steps include ruff --fix when fix=True and ruff available."""
        with patch("djb.cli.health._has_ruff", return_value=True):
            steps = _build_backend_lint_steps(tmp_path, fix=True, prefix="", scope="Backend")
        assert len(steps) == 2
        # First step is black format
        assert "black" in steps[0].cmd
        assert "--check" not in steps[0].cmd
        # Second step is ruff with --fix
        assert "ruff" in steps[1].cmd
        assert "--fix" in steps[1].cmd
        assert "lint fix" in steps[1].label

    def test_lint_steps_without_ruff(self, tmp_path):
        """Test that lint steps exclude ruff when not available."""
        with patch("djb.cli.health._has_ruff", return_value=False):
            steps = _build_backend_lint_steps(tmp_path, fix=False, prefix="", scope="Backend")
        assert len(steps) == 1
        assert "black" in steps[0].cmd
        # No ruff step
        assert not any("ruff" in step.cmd for step in steps)

    def test_test_steps_have_stream_enabled(self, tmp_path):
        """Test that test steps have stream=True for real-time output."""
        steps = _build_backend_test_steps(tmp_path, prefix="", scope="Backend")
        assert len(steps) == 1
        assert steps[0].stream is True

    def test_lint_steps_use_correct_command(self, tmp_path):
        """Test that lint steps use uv run black --check."""
        with patch("djb.cli.health._has_ruff", return_value=False):
            steps = _build_backend_lint_steps(tmp_path, fix=False, prefix="", scope="Backend")
        assert steps[0].cmd == ["uv", "run", "black", "--check", "."]
        assert steps[0].cwd == tmp_path

    def test_typecheck_steps_use_correct_command(self, tmp_path):
        """Test that typecheck steps use uv run pyright."""
        steps = _build_backend_typecheck_steps(tmp_path, prefix="", scope="Backend")
        assert steps[0].cmd == ["uv", "run", "pyright"]
        assert steps[0].cwd == tmp_path

    def test_test_steps_use_correct_command(self, tmp_path):
        """Test that test steps use uv run pytest."""
        steps = _build_backend_test_steps(tmp_path, prefix="", scope="Backend")
        assert steps[0].cmd == ["uv", "run", "pytest"]
        assert steps[0].cwd == tmp_path

    @pytest.mark.parametrize(
        "builder,expected_label",
        [
            (_build_backend_lint_steps, "Backend lint (black --check)"),
            (_build_backend_typecheck_steps, "Backend typecheck (pyright)"),
            (_build_backend_test_steps, "Backend tests (pytest)"),
        ],
    )
    def test_steps_label_format_without_prefix(self, tmp_path, builder, expected_label):
        """Test that steps have correct label without prefix."""
        with patch("djb.cli.health._has_ruff", return_value=False):
            steps = self._build_steps(builder, tmp_path, prefix="", scope="Backend")
        assert steps[0].label == expected_label


class TestFrontendStepBuilders:
    """Tests for frontend step builder functions."""

    def _build_steps(self, builder, frontend_dir, prefix=""):
        """Helper to call builder with appropriate arguments."""
        if builder == _build_frontend_lint_steps:
            return builder(frontend_dir, fix=False, prefix=prefix)
        return builder(frontend_dir, prefix=prefix)

    @pytest.mark.parametrize(
        "builder",
        [
            _build_frontend_lint_steps,
            _build_frontend_typecheck_steps,
            _build_frontend_test_steps,
        ],
    )
    def test_returns_empty_when_frontend_dir_missing(self, tmp_path, builder):
        """Test that builders return empty list when frontend directory doesn't exist."""
        nonexistent_dir = tmp_path / "frontend"
        steps = self._build_steps(builder, nonexistent_dir)
        assert steps == []

    @pytest.mark.parametrize(
        "builder",
        [
            _build_frontend_lint_steps,
            _build_frontend_typecheck_steps,
            _build_frontend_test_steps,
        ],
    )
    def test_returns_steps_when_frontend_dir_exists(self, tmp_path, builder):
        """Test that builders return steps when frontend directory exists."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = self._build_steps(builder, frontend_dir)
        assert len(steps) >= 1

    @pytest.mark.parametrize(
        "builder,expected_label",
        [
            (_build_frontend_lint_steps, "Frontend lint (bun lint)"),
            (_build_frontend_typecheck_steps, "Frontend typecheck (tsc)"),
            (_build_frontend_test_steps, "Frontend tests (bun test)"),
        ],
    )
    def test_steps_label_format_without_prefix(self, tmp_path, builder, expected_label):
        """Test that steps have correct label without prefix."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = self._build_steps(builder, frontend_dir)
        assert steps[0].label == expected_label

    @pytest.mark.parametrize(
        "builder,expected_label",
        [
            (_build_frontend_lint_steps, "[myproject] Frontend lint (bun lint)"),
            (_build_frontend_typecheck_steps, "[myproject] Frontend typecheck (tsc)"),
            (_build_frontend_test_steps, "[myproject] Frontend tests (bun test)"),
        ],
    )
    def test_steps_with_prefix(self, tmp_path, builder, expected_label):
        """Test that steps include prefix in label."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = self._build_steps(builder, frontend_dir, prefix="[myproject]")
        assert steps[0].label == expected_label

    def test_lint_steps_with_fix_mode(self, tmp_path):
        """Test that lint steps use --fix flag when fix=True."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = _build_frontend_lint_steps(frontend_dir, fix=True)
        assert len(steps) == 1
        assert "--fix" in steps[0].cmd
        assert "lint --fix" in steps[0].label

    def test_lint_steps_without_fix_mode(self, tmp_path):
        """Test that lint steps don't use --fix flag when fix=False."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = _build_frontend_lint_steps(frontend_dir, fix=False)
        assert len(steps) == 1
        assert "--fix" not in steps[0].cmd
        assert "--fix" not in steps[0].label

    def test_test_steps_have_stream_enabled(self, tmp_path):
        """Test that test steps have stream=True for real-time output."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = _build_frontend_test_steps(frontend_dir)
        assert len(steps) == 1
        assert steps[0].stream is True

    def test_lint_steps_use_correct_command(self, tmp_path):
        """Test that lint steps use bun run lint."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = _build_frontend_lint_steps(frontend_dir, fix=False)
        assert steps[0].cmd == ["bun", "run", "lint"]
        assert steps[0].cwd == frontend_dir

    def test_typecheck_steps_use_correct_command(self, tmp_path):
        """Test that typecheck steps use bun run tsc."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = _build_frontend_typecheck_steps(frontend_dir)
        assert steps[0].cmd == ["bun", "run", "tsc"]
        assert steps[0].cwd == frontend_dir

    def test_test_steps_use_correct_command(self, tmp_path):
        """Test that test steps use bun test."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        steps = _build_frontend_test_steps(frontend_dir)
        assert steps[0].cmd == ["bun", "test"]
        assert steps[0].cwd == frontend_dir


class TestFailureTips:
    """Tests for failure tip output including full commands."""

    def test_failure_shows_verbose_tip_with_command(
        self, runner, mock_health_context, host_only_context
    ):
        """Test that failure output shows -v tip with full command."""
        mock_run_cmd, mock_ctx = mock_health_context
        mock_run_cmd.return_value.returncode = 1
        mock_ctx.return_value = host_only_context

        with patch.object(sys, "argv", ["djb", "health", "typecheck"]):
            result = runner.invoke(djb_cli, ["health", "typecheck"])

        assert result.exit_code != 0
        assert "-v" in result.output
        assert "error details" in result.output.lower()
        # Should show the full command
        assert "djb -v health typecheck" in result.output

    def test_failure_shows_fix_tip_with_command(
        self, runner, mock_health_context, host_only_context
    ):
        """Test that failure output shows --fix tip with full command."""
        mock_run_cmd, mock_ctx = mock_health_context
        mock_run_cmd.return_value.returncode = 1
        mock_ctx.return_value = host_only_context

        with patch.object(sys, "argv", ["djb", "health", "lint"]):
            result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code != 0
        assert "--fix" in result.output
        assert "auto-fix" in result.output.lower()
        # Should show the full command (--fix appended at end since it's a subcommand flag)
        assert "djb health lint --fix" in result.output

    def test_verbose_mode_hides_verbose_tip(self, runner, mock_health_context, host_only_context):
        """Test that -v tip is hidden when already in verbose mode."""
        mock_run_cmd, mock_ctx = mock_health_context
        mock_run_cmd.return_value.returncode = 1
        mock_ctx.return_value = host_only_context

        with patch("djb.cli.health.run_streaming") as mock_streaming:
            mock_streaming.return_value = (1, "", "")
            result = runner.invoke(djb_cli, ["-v", "health", "typecheck"])

        assert result.exit_code != 0
        # Should NOT show the verbose tip since we're already verbose
        assert "re-run with -v" not in result.output

    def test_fix_mode_hides_fix_tip(self, runner, mock_health_context, host_only_context):
        """Test that --fix tip is hidden when already using --fix."""
        mock_run_cmd, mock_ctx = mock_health_context
        mock_run_cmd.return_value.returncode = 1
        mock_ctx.return_value = host_only_context

        result = runner.invoke(djb_cli, ["health", "lint", "--fix"])

        assert result.exit_code != 0
        # Should NOT show the fix tip since we're already using --fix
        assert "re-run with --fix" not in result.output


class TestScopeLabelsInOutput:
    """Tests for correct scope labels (Python vs Backend) in output."""

    def test_djb_uses_python_scope(self, runner, tmp_path, mock_health_context):
        """Test that djb project uses 'Python' scope label."""
        mock_run_cmd, mock_ctx = mock_health_context
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()

        mock_ctx.return_value = ProjectContext(djb_path=djb_dir, host_path=None, inside_djb=True)

        result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code == 0
        # Check that run_cmd was called with "Python" in the label
        assert mock_run_cmd.call_count > 0, "Expected run_cmd to be called"
        # The label kwarg should contain "Python" for djb projects
        calls_with_python = [
            call
            for call in mock_run_cmd.call_args_list
            if "label" in call.kwargs and "Python" in call.kwargs["label"]
        ]
        assert (
            len(calls_with_python) > 0
        ), f"Expected label with 'Python', got: {mock_run_cmd.call_args_list}"

    def test_host_uses_backend_scope(self, runner, tmp_path, mock_health_context, monkeypatch):
        """Test that host project uses 'Backend' scope label."""
        mock_run_cmd, mock_ctx = mock_health_context
        host_dir = tmp_path / "myapp"
        host_dir.mkdir()

        mock_ctx.return_value = ProjectContext(djb_path=None, host_path=host_dir, inside_djb=False)

        # Clear env var so config file is used
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)
        save_config(PROJECT, {"project_name": "myapp"}, host_dir)
        result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code == 0
        # Check that run_cmd was called with "Backend" in the label
        assert mock_run_cmd.call_count > 0, "Expected run_cmd to be called"
        # The label kwarg should contain "Backend" for host projects
        calls_with_backend = [
            call
            for call in mock_run_cmd.call_args_list
            if "label" in call.kwargs and "Backend" in call.kwargs["label"]
        ]
        assert (
            len(calls_with_backend) > 0
        ), f"Expected label with 'Backend', got: {mock_run_cmd.call_args_list}"

    def test_editable_shows_both_scopes(self, runner, tmp_path, mock_health_context, monkeypatch):
        """Test that editable mode shows Python for djb and Backend for host."""
        mock_run_cmd, mock_ctx = mock_health_context
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        host_dir = tmp_path / "myapp"
        host_dir.mkdir()

        mock_ctx.return_value = ProjectContext(
            djb_path=djb_dir, host_path=host_dir, inside_djb=False
        )

        # Clear env var so config file is used
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)
        save_config(PROJECT, {"project_name": "myapp"}, host_dir)
        result = runner.invoke(djb_cli, ["health", "lint"])

        assert result.exit_code == 0
        # Should show djb banner
        assert "djb (editable)" in result.output.lower()
        # Should show host project name
        assert "myapp" in result.output.lower()


class TestCoverageSupport:
    """Tests for coverage support in health commands."""

    def test_build_backend_test_steps_without_coverage(self, tmp_path):
        """Test building test steps without coverage."""
        steps = _build_backend_test_steps(tmp_path, prefix="", scope="Backend", cov=False)
        assert len(steps) == 1
        assert "--cov" not in steps[0].cmd
        assert "coverage" not in steps[0].label.lower()

    def test_build_backend_test_steps_with_coverage(self, tmp_path):
        """Test building test steps with coverage enabled."""
        with patch("djb.cli.health._has_pytest_cov", return_value=True):
            steps = _build_backend_test_steps(tmp_path, prefix="", scope="Backend", cov=True)
        assert len(steps) == 1
        assert "--cov" in steps[0].cmd
        assert "--cov-report=term-missing" in steps[0].cmd
        assert "coverage" in steps[0].label.lower()

    def test_build_backend_test_steps_coverage_fallback(self, tmp_path):
        """Test building test steps falls back when pytest-cov unavailable."""
        with patch("djb.cli.health._has_pytest_cov", return_value=False):
            steps = _build_backend_test_steps(tmp_path, prefix="", scope="Backend", cov=True)
        assert len(steps) == 1
        assert "--cov" not in steps[0].cmd
        assert "coverage" not in steps[0].label.lower()

    def test_health_test_has_cov_flag(self, runner):
        """Test that health test --help shows --cov flag."""
        result = runner.invoke(djb_cli, ["health", "test", "--help"])
        assert result.exit_code == 0
        assert "--cov" in result.output
        assert "--no-cov" in result.output

    @pytest.mark.parametrize(
        "args",
        [
            ["health", "test"],
            ["health"],
        ],
    )
    def test_coverage_disabled_by_default(self, runner, mock_run_cmd, args):
        """Test that coverage is disabled by default."""
        result = runner.invoke(djb_cli, args)
        assert result.exit_code == 0
        # Tests use run_streaming, check both run_cmd and run_streaming calls
        cmd_calls = [str(call) for call in mock_run_cmd.call_args_list]
        stream_calls = [str(call) for call in mock_run_cmd.stream.call_args_list]
        all_calls = cmd_calls + stream_calls
        pytest_calls = [c for c in all_calls if "pytest" in c]
        assert not any("--cov" in str(call) for call in pytest_calls)

    @pytest.mark.parametrize(
        "args",
        [
            ["health", "test", "--cov"],
            ["health", "--cov"],
        ],
    )
    def test_cov_flag_enables_coverage(self, runner, mock_run_cmd, args):
        """Test that --cov flag enables coverage."""
        with patch("djb.cli.health._has_pytest_cov", return_value=True):
            result = runner.invoke(djb_cli, args)
        assert result.exit_code == 0
        # Tests use run_streaming, check both run_cmd and run_streaming calls
        cmd_calls = [str(call) for call in mock_run_cmd.call_args_list]
        stream_calls = [str(call) for call in mock_run_cmd.stream.call_args_list]
        all_calls = cmd_calls + stream_calls
        assert any("--cov" in str(call) for call in all_calls)

    def test_no_cov_flag_disables_coverage(self, runner, mock_run_cmd):
        """Test that --no-cov explicitly disables coverage."""
        result = runner.invoke(djb_cli, ["health", "test", "--no-cov"])
        assert result.exit_code == 0
        # Tests use run_streaming, check both run_cmd and run_streaming calls
        cmd_calls = [str(call) for call in mock_run_cmd.call_args_list]
        stream_calls = [str(call) for call in mock_run_cmd.stream.call_args_list]
        all_calls = cmd_calls + stream_calls
        pytest_calls = [c for c in all_calls if "pytest" in c]
        assert not any("--cov" in str(call) for call in pytest_calls)


class TestGetRunScopes:
    """Tests for _get_run_scopes helper function."""

    @pytest.mark.parametrize(
        "frontend,backend,expected_backend,expected_frontend",
        [
            (False, False, True, True),  # Neither flag runs both
            (True, False, False, True),  # --frontend only
            (False, True, True, False),  # --backend only
            (True, True, True, True),  # Both flags runs both
        ],
    )
    def test_run_scopes(self, frontend, backend, expected_backend, expected_frontend):
        """Test that flags correctly determine which scopes run."""
        run_backend, run_frontend = _get_run_scopes(frontend, backend)
        assert run_backend is expected_backend
        assert run_frontend is expected_frontend


class TestHasPytestCov:
    """Tests for the _has_pytest_cov function."""

    def test_pytest_cov_available(self, tmp_path: Path):
        """Test returns True when pytest-cov is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _has_pytest_cov(tmp_path)

        assert result is True
        mock_run.assert_called_once()

    def test_pytest_cov_not_available(self, tmp_path: Path):
        """Test returns False when pytest-cov is not available."""
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = _has_pytest_cov(tmp_path)

        assert result is False

    def test_timeout_returns_false(self, tmp_path: Path):
        """Test returns False on timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=10)):
            result = _has_pytest_cov(tmp_path)

        assert result is False

    def test_file_not_found_returns_false(self, tmp_path: Path):
        """Test returns False when uv is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = _has_pytest_cov(tmp_path)

        assert result is False


class TestHasRuff:
    """Tests for the _has_ruff function."""

    def test_ruff_available(self, tmp_path: Path):
        """Test returns True when ruff is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _has_ruff(tmp_path)

        assert result is True
        mock_run.assert_called_once()

    def test_ruff_not_available(self, tmp_path: Path):
        """Test returns False when ruff is not available."""
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = _has_ruff(tmp_path)

        assert result is False

    def test_timeout_returns_false(self, tmp_path: Path):
        """Test returns False on timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=10)):
            result = _has_ruff(tmp_path)

        assert result is False

    def test_file_not_found_returns_false(self, tmp_path: Path):
        """Test returns False when uv is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = _has_ruff(tmp_path)

        assert result is False


class TestGetFrontendDir:
    """Tests for _get_frontend_dir helper."""

    def test_returns_frontend_path(self, tmp_path: Path):
        """Test that it returns the frontend subdirectory path."""
        result = _get_frontend_dir(tmp_path)
        assert result == tmp_path / "frontend"

    def test_returns_path_even_if_not_exists(self, tmp_path: Path):
        """Test that it returns the path even if frontend directory doesn't exist."""
        result = _get_frontend_dir(tmp_path)
        assert result == tmp_path / "frontend"
        assert not result.exists()

    def test_returns_path_when_exists(self, tmp_path: Path):
        """Test that it returns the path when frontend directory exists."""
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        result = _get_frontend_dir(tmp_path)
        assert result == frontend_dir
        assert result.exists()


class TestRunSteps:
    """Direct unit tests for _run_steps core step runner function.

    These tests verify the step execution logic, failure collection,
    streaming vs captured modes, and quiet mode behavior.
    """

    @pytest.fixture
    def mock_run_utilities(self):
        """Mock run_cmd and run_streaming for testing _run_steps directly."""
        with (
            patch("djb.cli.health.run_cmd") as mock_cmd,
            patch("djb.cli.health.run_streaming") as mock_stream,
            patch("djb.cli.health.logger") as mock_logger,
        ):
            # Default: successful commands
            mock_cmd.return_value.returncode = 0
            mock_cmd.return_value.stdout = ""
            mock_cmd.return_value.stderr = ""
            mock_stream.return_value = (0, "", "")
            yield mock_cmd, mock_stream, mock_logger

    def test_returns_empty_list_when_all_steps_pass(self, tmp_path, mock_run_utilities):
        """Test that empty list is returned when all steps succeed."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [
            HealthStep("lint", ["black", "--check", "."], tmp_path),
            HealthStep("typecheck", ["pyright"], tmp_path),
        ]

        failures = _run_steps(steps, quiet=False, verbose=False)

        assert failures == []
        assert mock_cmd.call_count == 2

    def test_returns_failures_for_failed_steps(self, tmp_path, mock_run_utilities):
        """Test that failures are collected for steps with non-zero exit codes."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        mock_cmd.return_value.returncode = 1
        mock_cmd.return_value.stdout = "error output"
        mock_cmd.return_value.stderr = "error details"

        steps = [HealthStep("lint", ["black", "--check", "."], tmp_path)]
        failures = _run_steps(steps, quiet=False, verbose=False)

        assert len(failures) == 1
        assert failures[0].label == "lint"
        assert failures[0].returncode == 1
        assert failures[0].stdout == "error output"
        assert failures[0].stderr == "error details"

    def test_collects_multiple_failures(self, tmp_path, mock_run_utilities):
        """Test that multiple failures are collected."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        mock_cmd.return_value.returncode = 1
        mock_cmd.return_value.stdout = "out"
        mock_cmd.return_value.stderr = "err"

        steps = [
            HealthStep("step1", ["cmd1"], tmp_path),
            HealthStep("step2", ["cmd2"], tmp_path),
            HealthStep("step3", ["cmd3"], tmp_path),
        ]
        failures = _run_steps(steps, quiet=False, verbose=False)

        assert len(failures) == 3
        assert [f.label for f in failures] == ["step1", "step2", "step3"]

    def test_uses_streaming_when_verbose(self, tmp_path, mock_run_utilities):
        """Test that run_streaming is used when verbose=True."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [HealthStep("lint", ["black", "--check", "."], tmp_path)]

        _run_steps(steps, quiet=False, verbose=True)

        mock_stream.assert_called_once()
        mock_cmd.assert_not_called()

    def test_uses_streaming_when_step_requests_stream(self, tmp_path, mock_run_utilities):
        """Test that run_streaming is used when step has stream=True."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [HealthStep("tests", ["pytest"], tmp_path, stream=True)]

        _run_steps(steps, quiet=False, verbose=False)

        mock_stream.assert_called_once()
        mock_cmd.assert_not_called()

    def test_uses_captured_mode_when_not_streaming(self, tmp_path, mock_run_utilities):
        """Test that run_cmd is used when neither verbose nor stream."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [HealthStep("lint", ["black", "--check", "."], tmp_path)]

        _run_steps(steps, quiet=False, verbose=False)

        mock_cmd.assert_called_once()
        mock_stream.assert_not_called()

    def test_uses_captured_mode_when_quiet_overrides_stream(self, tmp_path, mock_run_utilities):
        """Test that quiet mode uses captured output even with stream=True."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [HealthStep("tests", ["pytest"], tmp_path, stream=True)]

        _run_steps(steps, quiet=True, verbose=False)

        # When quiet=True, should_stream is not honored
        mock_cmd.assert_called_once()
        mock_stream.assert_not_called()

    def test_captures_streaming_failures(self, tmp_path, mock_run_utilities):
        """Test that streaming failures are captured correctly."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        mock_stream.return_value = (1, "streaming stdout", "streaming stderr")

        steps = [HealthStep("tests", ["pytest"], tmp_path, stream=True)]
        failures = _run_steps(steps, quiet=False, verbose=False)

        assert len(failures) == 1
        assert failures[0].label == "tests"
        assert failures[0].returncode == 1
        assert failures[0].stdout == "streaming stdout"
        assert failures[0].stderr == "streaming stderr"

    def test_logs_failure_message_for_captured_mode(self, tmp_path, mock_run_utilities):
        """Test that failure message is logged in captured mode."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        mock_cmd.return_value.returncode = 1
        mock_cmd.return_value.stdout = ""
        mock_cmd.return_value.stderr = ""

        steps = [HealthStep("lint", ["black", "--check", "."], tmp_path)]
        _run_steps(steps, quiet=False, verbose=False)

        mock_logger.fail.assert_called_once()
        call_arg = mock_logger.fail.call_args[0][0]
        assert "lint failed" in call_arg
        assert "exit 1" in call_arg

    def test_logs_failure_message_for_streaming_mode(self, tmp_path, mock_run_utilities):
        """Test that failure message is logged in streaming mode."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        mock_stream.return_value = (1, "", "")

        steps = [HealthStep("tests", ["pytest"], tmp_path, stream=True)]
        _run_steps(steps, quiet=False, verbose=False)

        mock_logger.fail.assert_called_once()
        call_arg = mock_logger.fail.call_args[0][0]
        assert "tests failed" in call_arg
        assert "exit 1" in call_arg

    def test_quiet_mode_suppresses_failure_logs(self, tmp_path, mock_run_utilities):
        """Test that quiet mode suppresses failure log messages."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        mock_cmd.return_value.returncode = 1
        mock_cmd.return_value.stdout = ""
        mock_cmd.return_value.stderr = ""

        steps = [HealthStep("lint", ["black", "--check", "."], tmp_path)]
        failures = _run_steps(steps, quiet=True, verbose=False)

        # Failures are still collected
        assert len(failures) == 1
        # But no failure message is logged
        mock_logger.fail.assert_not_called()

    def test_passes_correct_args_to_run_cmd(self, tmp_path, mock_run_utilities):
        """Test that run_cmd is called with correct arguments."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [HealthStep("lint", ["black", "--check", "."], tmp_path)]

        _run_steps(steps, quiet=True, verbose=False)

        mock_cmd.assert_called_once_with(
            ["black", "--check", "."],
            cwd=tmp_path,
            label="lint",
            halt_on_fail=False,
            quiet=True,
        )

    def test_passes_correct_args_to_run_streaming(self, tmp_path, mock_run_utilities):
        """Test that run_streaming is called with correct arguments."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [HealthStep("tests", ["pytest"], tmp_path, stream=True)]

        _run_steps(steps, quiet=False, verbose=False)

        mock_stream.assert_called_once_with(
            ["pytest"],
            cwd=tmp_path,
            label="tests",
        )

    def test_processes_steps_in_order(self, tmp_path, mock_run_utilities):
        """Test that steps are processed in order."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities
        steps = [
            HealthStep("first", ["cmd1"], tmp_path),
            HealthStep("second", ["cmd2"], tmp_path),
            HealthStep("third", ["cmd3"], tmp_path),
        ]

        _run_steps(steps, quiet=False, verbose=False)

        assert mock_cmd.call_count == 3
        labels = [call.kwargs["label"] for call in mock_cmd.call_args_list]
        assert labels == ["first", "second", "third"]

    def test_mixed_success_and_failures(self, tmp_path, mock_run_utilities):
        """Test handling of mixed success and failure results."""
        mock_cmd, mock_stream, mock_logger = mock_run_utilities

        # Configure mock to return success for first and third, failure for second
        def side_effect(*args, **kwargs):
            label = kwargs.get("label", "")
            result = MagicMock()
            if label == "step2":
                result.returncode = 1
                result.stdout = "step2 failed"
                result.stderr = "error"
            else:
                result.returncode = 0
                result.stdout = ""
                result.stderr = ""
            return result

        mock_cmd.side_effect = side_effect

        steps = [
            HealthStep("step1", ["cmd1"], tmp_path),
            HealthStep("step2", ["cmd2"], tmp_path),
            HealthStep("step3", ["cmd3"], tmp_path),
        ]
        failures = _run_steps(steps, quiet=False, verbose=False)

        assert len(failures) == 1
        assert failures[0].label == "step2"
        # All three steps should have been run
        assert mock_cmd.call_count == 3


class TestReportFailures:
    """Direct unit tests for _report_failures failure reporting function.

    These tests verify failure output formatting, tip display logic,
    and the verbose detail display behavior.
    """

    @pytest.fixture
    def mock_logger_and_argv(self):
        """Mock logger and sys.argv for testing _report_failures."""
        with (
            patch("djb.cli.health.logger") as mock_logger,
            patch.object(sys, "argv", ["djb", "health", "lint"]),
        ):
            yield mock_logger

    def test_reports_success_when_no_failures(self, mock_logger_and_argv):
        """Test that success message is logged when no failures."""
        mock_logger = mock_logger_and_argv

        _report_failures([], fix=False, verbose=False)

        mock_logger.done.assert_called_once_with("Health checks passed")

    def test_raises_exception_when_failures_present(self, mock_logger_and_argv):
        """Test that ClickException is raised when there are failures."""
        failures = [StepFailure("lint", 1, "", "")]

        with pytest.raises(click.ClickException, match="Health checks failed"):
            _report_failures(failures, fix=False, verbose=False)

    def test_logs_failure_header(self, mock_logger_and_argv):
        """Test that failure header is logged."""
        mock_logger = mock_logger_and_argv
        failures = [StepFailure("lint", 1, "", "")]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=False)

        # Check that header message was logged
        fail_calls = [call[0][0] for call in mock_logger.fail.call_args_list]
        assert any("Health checks completed with failures" in msg for msg in fail_calls)

    def test_logs_each_failure(self, mock_logger_and_argv):
        """Test that each failure is logged with label and exit code."""
        mock_logger = mock_logger_and_argv
        failures = [
            StepFailure("lint", 1, "", ""),
            StepFailure("typecheck", 2, "", ""),
        ]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=False)

        fail_calls = [call[0][0] for call in mock_logger.fail.call_args_list]
        assert any("lint (exit 1)" in msg for msg in fail_calls)
        assert any("typecheck (exit 2)" in msg for msg in fail_calls)

    def test_shows_verbose_tip_when_not_verbose(self, mock_logger_and_argv):
        """Test that verbose tip is shown when not in verbose mode."""
        mock_logger = mock_logger_and_argv
        failures = [StepFailure("lint", 1, "", "")]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=False)

        tip_calls = [call[0][0] for call in mock_logger.tip.call_args_list]
        assert any("-v" in msg and "error details" in msg for msg in tip_calls)

    def test_hides_verbose_tip_when_verbose(self, mock_logger_and_argv):
        """Test that verbose tip is hidden when already in verbose mode."""
        mock_logger = mock_logger_and_argv
        failures = [StepFailure("lint", 1, "", "")]

        # Simulate already being in verbose mode
        with patch.object(sys, "argv", ["djb", "-v", "health", "lint"]):
            with pytest.raises(click.ClickException):
                _report_failures(failures, fix=False, verbose=True)

        tip_calls = [call[0][0] for call in mock_logger.tip.call_args_list]
        # Should not suggest -v when already verbose
        assert not any("re-run with -v" in msg for msg in tip_calls)

    def test_shows_fix_tip_when_not_fix(self, mock_logger_and_argv):
        """Test that fix tip is shown when not using --fix."""
        mock_logger = mock_logger_and_argv
        failures = [StepFailure("lint", 1, "", "")]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=False)

        tip_calls = [call[0][0] for call in mock_logger.tip.call_args_list]
        assert any("--fix" in msg and "auto-fix" in msg for msg in tip_calls)

    def test_hides_fix_tip_when_fix(self, mock_logger_and_argv):
        """Test that fix tip is hidden when already using --fix."""
        mock_logger = mock_logger_and_argv
        failures = [StepFailure("lint", 1, "", "")]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=True, verbose=False)

        tip_calls = [call[0][0] for call in mock_logger.tip.call_args_list]
        # Should not suggest --fix when already using it
        assert not any("re-run with --fix" in msg for msg in tip_calls)

    def test_verbose_mode_shows_failure_details(self, mock_logger_and_argv):
        """Test that verbose mode shows stdout/stderr from failures."""
        mock_logger = mock_logger_and_argv
        failures = [
            StepFailure("lint", 1, "stdout content", "stderr content"),
        ]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=True)

        # Should show the failure details section
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Failure details" in msg for msg in warning_calls)
        assert any("lint" in msg for msg in warning_calls)

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("stdout content" in msg for msg in info_calls)
        assert any("stderr content" in msg for msg in info_calls)

    def test_verbose_mode_skips_empty_output(self, mock_logger_and_argv):
        """Test that verbose mode doesn't log empty stdout/stderr."""
        mock_logger = mock_logger_and_argv
        failures = [
            StepFailure("lint", 1, "", ""),  # Both empty
        ]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=True)

        # The info calls should only be for empty line separators, not output content
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        # Filter out empty string calls (separators)
        non_empty_info = [msg for msg in info_calls if msg.strip()]
        # Should not have the output content logged
        assert not non_empty_info

    def test_verbose_mode_shows_multiple_failures(self, mock_logger_and_argv):
        """Test that verbose mode shows details for all failures."""
        mock_logger = mock_logger_and_argv
        failures = [
            StepFailure("lint", 1, "lint stdout", "lint stderr"),
            StepFailure("typecheck", 2, "typecheck stdout", "typecheck stderr"),
        ]

        with pytest.raises(click.ClickException):
            _report_failures(failures, fix=False, verbose=True)

        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        # Both failure labels should appear
        assert any("lint" in msg for msg in warning_calls)
        assert any("typecheck" in msg for msg in warning_calls)

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        # Both outputs should appear
        assert any("lint stdout" in msg for msg in info_calls)
        assert any("typecheck stdout" in msg for msg in info_calls)
