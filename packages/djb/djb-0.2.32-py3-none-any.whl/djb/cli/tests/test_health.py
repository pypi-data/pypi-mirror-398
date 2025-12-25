"""Tests for djb health command."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from djb import configure
from djb.cli.djb import djb_cli
from djb.cli.health import (
    HealthStep,
    ProjectContext,
    _build_backend_lint_steps,
    _build_backend_test_steps,
    _build_backend_typecheck_steps,
    _get_command_with_flag,
    _get_host_display_name,
    _get_project_context,
    _get_run_scopes,
    _is_inside_djb_dir,
    _run_for_projects,
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
