"""Health check commands for running lint, typecheck, and tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable, NamedTuple

import click

from djb import config
from djb.config import config_for_project
from djb.cli.context import CliHealthContext, pass_context
from djb.cli.editable import (
    get_djb_source_path,
    is_djb_editable,
    is_djb_package_dir,
)
from djb.cli.find_overlap import run_find_overlap
from djb.core.logging import get_logger
from djb.cli.utils import run_cmd, run_streaming

logger = get_logger(__name__)


def _has_pytest_cov(project_root: Path) -> bool:
    """Check if pytest-cov is available in the project's environment."""
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import pytest_cov"],
            cwd=project_root,
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


class HealthStep(NamedTuple):
    """A single health check step to execute."""

    label: str
    cmd: list[str]
    cwd: Path | None = None
    stream: bool = False  # If True, stream output even without -v flag (for test progress)


class ProjectContext(NamedTuple):
    """Context for which projects to run health checks on."""

    djb_path: Path | None  # Path to djb if we should check it
    host_path: Path | None  # Path to host project if we should check it
    inside_djb: bool  # True if running from inside djb directory


class StepFailure(NamedTuple):
    """A failed health check step with captured output."""

    label: str
    returncode: int
    stdout: str
    stderr: str


def _is_inside_djb_dir(path: Path) -> bool:
    """Check if the given path is inside the djb project directory."""
    return is_djb_package_dir(path)


def _get_run_scopes(scope_frontend: bool, scope_backend: bool) -> tuple[bool, bool]:
    """Determine which scopes to run based on flags.

    Args:
        scope_frontend: Whether --frontend flag was set
        scope_backend: Whether --backend flag was set

    Returns:
        Tuple of (run_backend, run_frontend). If neither flag is set, both are True.
    """
    neither_specified = not scope_frontend and not scope_backend
    run_frontend = scope_frontend or neither_specified
    run_backend = scope_backend or neither_specified
    return run_backend, run_frontend


def _get_project_context() -> ProjectContext:
    """Determine which projects to run health checks on.

    Returns a ProjectContext with:
    - djb_path: Path to djb if we should check it (editable or inside djb)
    - host_path: Path to host project if we should check it
    - inside_djb: True if running from inside djb directory

    Logic:
    1. If running from inside djb directory: only check djb, skip host
    2. If djb is editable in host project: check djb first, then host
    3. Otherwise: just check the current project (host)
    """
    project_root = config.project_dir

    # Check if we're inside the djb directory
    if _is_inside_djb_dir(project_root):
        return ProjectContext(djb_path=project_root, host_path=None, inside_djb=True)

    # Check if djb is installed in editable mode
    if is_djb_editable(project_root):
        djb_source = get_djb_source_path(project_root)
        if djb_source:
            djb_path = (project_root / djb_source).resolve()
            return ProjectContext(djb_path=djb_path, host_path=project_root, inside_djb=False)

    # Default: just check the host project
    return ProjectContext(djb_path=None, host_path=project_root, inside_djb=False)


def _get_frontend_dir(project_root: Path) -> Path:
    """Get frontend directory path."""
    return project_root / "frontend"


def _get_host_display_name(host_path: Path) -> str:
    """Get the display name for the host project.

    Uses the configured project name if available, otherwise falls back to directory name.
    """
    with config_for_project(host_path) as host_cfg:
        return host_cfg.project_name or host_path.name


def _run_steps(
    steps: list[HealthStep], quiet: bool = False, verbose: bool = False
) -> list[StepFailure]:
    """Run health check steps and return failures.

    Args:
        steps: List of health check steps to run
        quiet: Suppress all output
        verbose: Stream output in real-time (shows failures inline)

    Returns:
        List of StepFailure for any failed steps
    """
    failures: list[StepFailure] = []

    for step in steps:
        # Stream output if verbose flag or step requests streaming (e.g., tests)
        should_stream = verbose or step.stream
        if should_stream and not quiet:
            # Stream output in real-time
            returncode, stdout, stderr = run_streaming(
                step.cmd,
                cwd=step.cwd,
                label=step.label,
            )
            if returncode != 0:
                logger.fail(f"{step.label} failed (exit {returncode})")
                failures.append(StepFailure(step.label, returncode, stdout, stderr))
        else:
            # Capture output (quiet or normal mode)
            result = run_cmd(
                step.cmd,
                cwd=step.cwd,
                label=step.label,
                halt_on_fail=False,
                quiet=quiet,
            )
            if result.returncode != 0:
                if not quiet:
                    logger.fail(f"{step.label} failed (exit {result.returncode})")
                failures.append(
                    StepFailure(step.label, result.returncode, result.stdout, result.stderr)
                )

    return failures


def _get_command_with_flag(
    flag: str, skip_if_present: list[str] | None = None, append: bool = False
) -> str:
    """Construct a command string with a flag added.

    Uses sys.argv to get the original command and adds the flag.
    Always uses 'djb' as the program name regardless of how it was invoked.

    Args:
        flag: The flag to add (e.g., "-v" or "--fix")
        skip_if_present: List of flags that, if already present, skip insertion
        append: If True, append at end (for subcommand flags like --fix).
                If False, insert after 'djb' (for global flags like -v).
    """
    args = sys.argv[:]

    # Replace full path with just 'djb'
    args[0] = "djb"

    # Skip if any of the specified flags are already present
    if skip_if_present and any(f in args for f in skip_if_present):
        return " ".join(args)

    if append:
        # Append at end (for subcommand flags like --fix)
        args.append(flag)
    else:
        # Insert after program name (for global flags like -v)
        if len(args) > 1:
            args.insert(1, flag)
        else:
            args.append(flag)

    return " ".join(args)


def _report_failures(
    failures: list[StepFailure],
    fix: bool = False,
    verbose: bool = False,
) -> None:
    """Report failures and raise exception if any."""
    if failures:
        logger.info("")
        logger.fail("Health checks completed with failures:")
        for failure in failures:
            logger.fail(f"{failure.label} (exit {failure.returncode})")

        if verbose:
            logger.info("")
            logger.warning("=" * 60)
            logger.warning("Failure details:")
            logger.warning("=" * 60)
            for failure in failures:
                logger.warning(f"\n--- {failure.label} ---")
                if failure.stdout:
                    logger.info(failure.stdout)
                if failure.stderr:
                    logger.info(failure.stderr)

        # Show tips for how to fix or get more info
        tips: list[str] = []

        if not verbose:
            verbose_cmd = _get_command_with_flag("-v", skip_if_present=["-v", "--verbose"])
            tips.append(f"re-run with -v to see error details: {verbose_cmd}")

        if not fix:
            fix_cmd = _get_command_with_flag("--fix", skip_if_present=["--fix"], append=True)
            tips.append(f"re-run with --fix to attempt auto-fixes for lint issues: {fix_cmd}")

        if tips:
            logger.info("")
            for tip in tips:
                logger.tip(tip)

        raise click.ClickException("Health checks failed")

    logger.done("Health checks passed")


def _has_ruff(project_root: Path) -> bool:
    """Check if ruff is available in the project's environment."""
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "--version"],
            cwd=project_root,
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _build_backend_lint_steps(
    project_root: Path, fix: bool, prefix: str, scope: str
) -> list[HealthStep]:
    """Build backend lint steps for a project."""
    label_prefix = f"{prefix} " if prefix else ""
    steps = []

    if fix:
        steps.append(
            HealthStep(
                f"{label_prefix}{scope} format (black)", ["uv", "run", "black", "."], project_root
            )
        )
        if _has_ruff(project_root):
            steps.append(
                HealthStep(
                    f"{label_prefix}{scope} lint fix (ruff check --fix)",
                    ["uv", "run", "ruff", "check", "--fix", "."],
                    project_root,
                )
            )
    else:
        steps.append(
            HealthStep(
                f"{label_prefix}{scope} lint (black --check)",
                ["uv", "run", "black", "--check", "."],
                project_root,
            )
        )
        if _has_ruff(project_root):
            steps.append(
                HealthStep(
                    f"{label_prefix}{scope} lint (ruff check)",
                    ["uv", "run", "ruff", "check", "."],
                    project_root,
                )
            )

    return steps


def _build_backend_typecheck_steps(project_root: Path, prefix: str, scope: str) -> list[HealthStep]:
    """Build backend typecheck steps for a project."""
    label_prefix = f"{prefix} " if prefix else ""
    return [
        HealthStep(
            f"{label_prefix}{scope} typecheck (pyright)", ["uv", "run", "pyright"], project_root
        )
    ]


def _build_backend_test_steps(
    project_root: Path, prefix: str, scope: str, cov: bool = False
) -> list[HealthStep]:
    """Build backend test steps for a project."""
    label_prefix = f"{prefix} " if prefix else ""
    cmd = ["uv", "run", "pytest"]
    label_suffix = ""

    if cov:
        if _has_pytest_cov(project_root):
            cmd.extend(["--cov", "--cov-report=term-missing"])
            label_suffix = " with coverage"
        else:
            logger.notice(
                f"pytest-cov not installed in {project_root.name}, "
                "skipping coverage. Run: uv add --dev pytest-cov"
            )

    return [
        HealthStep(
            f"{label_prefix}{scope} tests (pytest{label_suffix})",
            cmd,
            project_root,
            stream=True,  # Show test progress in real-time
        )
    ]


def _build_frontend_lint_steps(frontend_dir: Path, fix: bool, prefix: str = "") -> list[HealthStep]:
    """Build frontend lint steps for a project."""
    if not frontend_dir.exists():
        return []
    label_prefix = f"{prefix} " if prefix else ""
    if fix:
        return [
            HealthStep(
                f"{label_prefix}Frontend lint (bun lint --fix)",
                ["bun", "run", "lint", "--fix"],
                frontend_dir,
            )
        ]
    return [
        HealthStep(f"{label_prefix}Frontend lint (bun lint)", ["bun", "run", "lint"], frontend_dir)
    ]


def _build_frontend_typecheck_steps(frontend_dir: Path, prefix: str = "") -> list[HealthStep]:
    """Build frontend typecheck steps for a project."""
    if not frontend_dir.exists():
        return []
    label_prefix = f"{prefix} " if prefix else ""
    return [
        HealthStep(f"{label_prefix}Frontend typecheck (tsc)", ["bun", "run", "tsc"], frontend_dir)
    ]


def _build_frontend_test_steps(frontend_dir: Path, prefix: str = "") -> list[HealthStep]:
    """Build frontend test steps for a project."""
    if not frontend_dir.exists():
        return []
    label_prefix = f"{prefix} " if prefix else ""
    return [
        HealthStep(
            f"{label_prefix}Frontend tests (bun test)",
            ["bun", "test"],
            frontend_dir,
            stream=True,  # Show test progress in real-time
        )
    ]


# Type alias for step builder callbacks used by _run_for_projects
StepBuilder = Callable[[Path, str, bool], list[HealthStep]]


def _run_for_projects(
    health_ctx: CliHealthContext,
    build_steps: StepBuilder,
    section_name: str,
    fix: bool = False,
) -> None:
    """Run a health subcommand across djb and host projects.

    This helper extracts the common pattern shared by lint, typecheck, test, and e2e
    subcommands. Each subcommand follows the same structure:
    1. Check for djb (editable) and run steps if present
    2. Check for host project and run steps if present
    3. Report failures

    Args:
        health_ctx: CLI health context with verbose/quiet flags and config.
        build_steps: Callback that takes (path, prefix, is_djb) and returns steps.
            - path: Project root path
            - prefix: Label prefix like "[djb]" or "[host_name]"
            - is_djb: True if building steps for djb, False for host project
        section_name: Name for logging sections (e.g., "lint", "typecheck").
        fix: Whether --fix flag is enabled (for _report_failures tip).
    """
    verbose = health_ctx.verbose
    quiet = health_ctx.quiet
    project_ctx = _get_project_context()
    all_failures: list[StepFailure] = []

    if project_ctx.djb_path:
        prefix = "[djb]" if project_ctx.host_path else ""
        if prefix and not quiet:
            logger.section(f"Running {section_name} for djb (editable)")
        steps = build_steps(project_ctx.djb_path, prefix, True)
        all_failures.extend(_run_steps(steps, quiet, verbose))

    if project_ctx.host_path:
        host_name = _get_host_display_name(project_ctx.host_path)
        prefix = f"[{host_name}]" if project_ctx.djb_path else ""
        if prefix and not quiet:
            logger.section(f"Running {section_name} for {host_name}")
        steps = build_steps(project_ctx.host_path, prefix, False)
        all_failures.extend(_run_steps(steps, quiet, verbose))

    if project_ctx.inside_djb and project_ctx.host_path is None and not quiet:
        logger.notice("Running from djb directory, skipping host project checks.")

    _report_failures(all_failures, fix=fix, verbose=verbose)


@click.group(invoke_without_command=True)
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to auto-fix lint/format issues.",
)
@click.option(
    "--cov",
    is_flag=True,
    help="Enable code coverage reporting for tests.",
)
@click.pass_context
def health(ctx: click.Context, fix: bool, cov: bool):
    """Run health checks: lint, typecheck, and tests.

    \b
    When run without a subcommand, executes all checks:
      * Linting (black for backend, bun lint for frontend)
      * Type checking (pyright for backend, tsc for frontend)
      * Tests (pytest for backend, bun test for frontend)

    \b
    Subcommands:
      lint       Run linting only
      typecheck  Run type checking only
      test       Run tests only
      e2e        Run E2E tests only

    \b
    Examples:
      djb health                    # Run all checks
      djb --backend health          # Backend checks only
      djb --frontend health         # Frontend checks only
      djb health lint --fix         # Run linting with auto-fix
      djb health typecheck          # Type checking only
      djb health test               # Tests only
      djb health test --cov         # Tests with coverage
      djb health e2e                # E2E tests only
      djb -v health                 # Show error details on failure
    """
    # Specialize context for health subcommands
    parent_context = ctx.obj
    ctx.obj = CliHealthContext()
    ctx.obj.__dict__.update(parent_context.__dict__)
    ctx.obj.fix = fix
    ctx.obj.cov = cov

    # If no subcommand, run all checks
    if ctx.invoked_subcommand is None:
        _run_all_checks(ctx.obj)


def _run_all_checks(health_ctx: CliHealthContext) -> None:
    """Run all health checks."""
    fix = health_ctx.fix
    cov = health_ctx.cov
    verbose = health_ctx.verbose
    quiet = health_ctx.quiet
    run_backend, run_frontend = _get_run_scopes(health_ctx.scope_frontend, health_ctx.scope_backend)

    project_ctx = _get_project_context()
    all_failures: list[StepFailure] = []

    # Run checks for djb if present
    if project_ctx.djb_path:
        prefix = "[djb]" if project_ctx.host_path else ""
        if prefix and not quiet:
            logger.section("Running health checks for djb (editable)")

        steps: list[HealthStep] = []
        djb_frontend = _get_frontend_dir(project_ctx.djb_path)

        if run_backend:
            steps.extend(
                _build_backend_lint_steps(project_ctx.djb_path, fix, prefix, scope="Python")
            )
            steps.extend(
                _build_backend_typecheck_steps(project_ctx.djb_path, prefix, scope="Python")
            )
            steps.extend(
                _build_backend_test_steps(project_ctx.djb_path, prefix, scope="Python", cov=cov)
            )

        if run_frontend:
            steps.extend(_build_frontend_lint_steps(djb_frontend, fix, prefix))
            steps.extend(_build_frontend_typecheck_steps(djb_frontend, prefix))
            steps.extend(_build_frontend_test_steps(djb_frontend, prefix))

        all_failures.extend(_run_steps(steps, quiet, verbose))

    # Run checks for host project if present
    if project_ctx.host_path:
        host_name = _get_host_display_name(project_ctx.host_path)
        prefix = f"[{host_name}]" if project_ctx.djb_path else ""
        if prefix and not quiet:
            logger.section(f"Running health checks for {host_name}")

        steps = []
        host_frontend = _get_frontend_dir(project_ctx.host_path)

        if run_backend:
            steps.extend(
                _build_backend_lint_steps(project_ctx.host_path, fix, prefix, scope="Backend")
            )
            steps.extend(
                _build_backend_typecheck_steps(project_ctx.host_path, prefix, scope="Backend")
            )
            steps.extend(
                _build_backend_test_steps(project_ctx.host_path, prefix, scope="Backend", cov=cov)
            )

        if run_frontend:
            steps.extend(_build_frontend_lint_steps(host_frontend, fix, prefix))
            steps.extend(_build_frontend_typecheck_steps(host_frontend, prefix))
            steps.extend(_build_frontend_test_steps(host_frontend, prefix))

        all_failures.extend(_run_steps(steps, quiet, verbose))

    # Show skip message if inside djb
    if project_ctx.inside_djb and project_ctx.host_path is None and not quiet:
        logger.notice("Running from djb directory, skipping host project checks.")

    _report_failures(all_failures, fix, verbose)


@health.command()
@click.option("--fix", is_flag=True, help="Attempt to auto-fix lint issues.")
@pass_context(CliHealthContext)
def lint(health_ctx: CliHealthContext, fix: bool):
    """Run linting checks.

    Backend: black (--check unless --fix)
    Frontend: bun run lint
    """
    fix = fix or health_ctx.fix
    run_backend, run_frontend = _get_run_scopes(health_ctx.scope_frontend, health_ctx.scope_backend)

    def build_steps(path: Path, prefix: str, is_djb: bool) -> list[HealthStep]:
        steps: list[HealthStep] = []
        frontend_dir = _get_frontend_dir(path)
        scope = "Python" if is_djb else "Backend"
        if run_backend:
            steps.extend(_build_backend_lint_steps(path, fix, prefix, scope=scope))
        if run_frontend:
            steps.extend(_build_frontend_lint_steps(frontend_dir, fix, prefix))
        return steps

    _run_for_projects(health_ctx, build_steps, "lint", fix=fix)


@health.command()
@pass_context(CliHealthContext)
def typecheck(health_ctx: CliHealthContext):
    """Run type checking.

    Backend: pyright
    Frontend: bun run tsc
    """
    run_backend, run_frontend = _get_run_scopes(health_ctx.scope_frontend, health_ctx.scope_backend)

    def build_steps(path: Path, prefix: str, is_djb: bool) -> list[HealthStep]:
        steps: list[HealthStep] = []
        frontend_dir = _get_frontend_dir(path)
        scope = "Python" if is_djb else "Backend"
        if run_backend:
            steps.extend(_build_backend_typecheck_steps(path, prefix, scope=scope))
        if run_frontend:
            steps.extend(_build_frontend_typecheck_steps(frontend_dir, prefix))
        return steps

    _run_for_projects(health_ctx, build_steps, "typecheck")


@health.group(invoke_without_command=True)
@click.option("--cov/--no-cov", default=False, help="Enable/disable code coverage reporting.")
@click.pass_context
def test(ctx: click.Context, cov: bool):
    """Run tests (excluding E2E).

    Backend: pytest
    Frontend: bun test

    Use --cov to enable code coverage reporting.

    Subcommands:
        overlap    Find tests with overlapping coverage
    """
    # If a subcommand was invoked, don't run the default behavior
    if ctx.invoked_subcommand is not None:
        return

    health_ctx = ctx.obj
    assert isinstance(health_ctx, CliHealthContext)
    # Combine local --cov flag with parent --cov flag from health group
    cov = cov or health_ctx.cov
    run_backend, run_frontend = _get_run_scopes(health_ctx.scope_frontend, health_ctx.scope_backend)

    def build_steps(path: Path, prefix: str, is_djb: bool) -> list[HealthStep]:
        steps: list[HealthStep] = []
        frontend_dir = _get_frontend_dir(path)
        scope = "Python" if is_djb else "Backend"
        if run_backend:
            steps.extend(_build_backend_test_steps(path, prefix, scope=scope, cov=cov))
        if run_frontend:
            steps.extend(_build_frontend_test_steps(frontend_dir, prefix))
        return steps

    _run_for_projects(health_ctx, build_steps, "tests")


@test.command("overlap")
@click.option(
    "--min-similarity",
    type=float,
    default=0.95,
    help="Minimum Jaccard similarity to report (0-1, default: 0.95)",
)
@click.option(
    "--show-pairs",
    is_flag=True,
    help="Show all overlapping test pairs instead of parametrization groups.",
)
@click.option(
    "-p",
    "--package",
    "packages",
    multiple=True,
    help="Package(s) to analyze (can be specified multiple times). Defaults to 'src'.",
)
@pass_context(CliHealthContext)
def overlap(
    health_ctx: CliHealthContext, min_similarity: float, show_pairs: bool, packages: tuple[str, ...]
):
    """Find tests with overlapping coverage for potential consolidation.

    Collects per-test coverage data and identifies tests in the same class
    that cover the same code paths. These are candidates for consolidation
    using @pytest.mark.parametrize.

    Examples:
        djb health test overlap
        djb health test overlap -p src/djb/cli -p src/djb/core
        djb health test overlap --min-similarity 0.90
    """
    project_ctx = _get_project_context()
    project_root = project_ctx.djb_path or project_ctx.host_path

    if not project_root:
        raise click.ClickException("No project directory found")

    run_find_overlap(project_root, min_similarity, show_pairs, list(packages) or None)


@health.command()
@pass_context(CliHealthContext)
def e2e(health_ctx: CliHealthContext):
    """Run E2E tests.

    For djb: Runs CLI E2E tests from tests/e2e/ directory.
    For host project: Runs pytest with --run-e2e flag for browser-based tests.
    """

    def build_steps(path: Path, prefix: str, is_djb: bool) -> list[HealthStep]:
        label_prefix = f"{prefix} " if prefix else ""
        if is_djb:
            # djb CLI E2E tests are in tests/e2e/
            return [
                HealthStep(
                    f"{label_prefix}E2E tests (pytest --run-e2e tests/e2e/)",
                    ["uv", "run", "pytest", "--run-e2e", "tests/e2e/"],
                    path,
                    stream=True,  # Show test progress in real-time
                )
            ]
        else:
            # Host project E2E tests (Selenium browser tests)
            return [
                HealthStep(
                    f"{label_prefix}E2E tests (pytest --run-e2e)",
                    ["uv", "run", "pytest", "--run-e2e"],
                    path,
                    stream=True,  # Show test progress in real-time
                )
            ]

    _run_for_projects(health_ctx, build_steps, "E2E tests")
