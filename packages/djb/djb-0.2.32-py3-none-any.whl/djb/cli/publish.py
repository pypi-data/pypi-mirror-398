"""
djb publish CLI - Version management and PyPI publishing.

Provides commands for bumping versions and publishing any Python package to PyPI.
"""

from __future__ import annotations

import re
import time
import tomllib
from collections.abc import Callable
from pathlib import Path

import click

from djb import config
from djb.core.logging import get_logger
from djb.cli.utils import run_cmd
from djb.cli.editable import (
    find_djb_dir,
    get_djb_source_path,
    is_djb_editable,
    is_djb_package_dir,
    uninstall_editable_djb,
)
from djb.cli.editable_stash import (
    bust_uv_cache,
    regenerate_uv_lock,
    restore_editable,
)

logger = get_logger(__name__)


def get_package_info(package_root: Path) -> tuple[str, str]:
    """Read package name and version from pyproject.toml.

    Returns:
        Tuple of (package_name, version)
    """
    pyproject = package_root / "pyproject.toml"
    if not pyproject.exists():
        raise click.ClickException(f"No pyproject.toml found in {package_root}")

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    name = project.get("name")
    version = project.get("version")

    if not name:
        raise click.ClickException(f"No project name found in {pyproject}")
    if not version:
        raise click.ClickException(f"No project version found in {pyproject}")

    return name, version


def find_version_file(package_root: Path, package_name: str) -> Path | None:
    """Find _version.py in common locations.

    Supports both src/ layout and flat layout.

    Args:
        package_root: Root directory of the package
        package_name: Package name (e.g., "django-model-changes")

    Returns:
        Path to _version.py if found, None otherwise
    """
    # Convert package name to directory (django-model-changes -> django_model_changes)
    pkg_dir = package_name.replace("-", "_")
    candidates = [
        package_root / "src" / pkg_dir / "_version.py",  # src layout (djb)
        package_root / pkg_dir / "_version.py",  # flat layout (django_model_changes)
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def get_version(package_root: Path) -> str:
    """Read current version from pyproject.toml."""
    _, version = get_package_info(package_root)
    return version


def set_version(package_root: Path, package_name: str, version: str) -> None:
    """Write new version to pyproject.toml and _version.py."""
    # Update pyproject.toml
    pyproject = package_root / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")

    new_content = re.sub(
        r'^(version\s*=\s*)"[^"]+"',
        f'\\1"{version}"',
        content,
        flags=re.MULTILINE,
    )

    pyproject.write_text(new_content, encoding="utf-8")

    # Update _version.py if it exists
    version_file = find_version_file(package_root, package_name)
    if version_file:
        version_content = f'''"""Version information for {package_name}.

This file is automatically updated by `djb publish`.
"""

__version__ = "{version}"
'''
        version_file.write_text(version_content, encoding="utf-8")


def bump_version(version: str, part: str) -> str:
    """Bump the specified part of a semver version string.

    Args:
        version: Current version (e.g., "0.2.0")
        part: Which part to bump ("major", "minor", or "patch")

    Returns:
        New version string
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise click.ClickException(f"Invalid version format: {version} (expected X.Y.Z)")

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise click.ClickException(f"Unknown version part: {part}")

    return f"{major}.{minor}.{patch}"


def is_dependency_of(package_name: str, host_root: Path) -> bool:
    """Check if package_name is listed as a dependency of the host project."""
    pyproject = host_root / "pyproject.toml"
    if not pyproject.exists():
        return False
    content = pyproject.read_text()
    # Match patterns like "package-name>=1.0" or 'package-name>=1.0' or "package-name"
    pattern = rf'["\']?{re.escape(package_name)}[><=!~\s\d.,]*["\']?'
    return bool(re.search(pattern, content))


def wait_for_uv_resolvable(
    repo_root: Path,
    version: str,
    timeout: int = 300,
    initial_interval: int = 5,
    max_interval: int = 30,
) -> bool:
    """Wait until uv can resolve the new package version from PyPI.

    After pushing a new version to PyPI, there's a delay before the package
    index is updated and uv can resolve it. This function retries `uv lock`
    until it succeeds, which is the definitive test that the version is available.

    Uses exponential backoff to reduce load on PyPI while waiting.

    Args:
        repo_root: Path to the project root (where pyproject.toml is)
        version: The version waiting for (used for logging)
        timeout: Maximum time to wait in seconds (default: 5 minutes)
        initial_interval: Initial time between retries in seconds (default: 5)
        max_interval: Maximum time between retries in seconds (default: 30)

    Returns:
        True if uv lock succeeds within the timeout, False otherwise
    """
    start_time = time.time()
    interval = initial_interval

    while time.time() - start_time < timeout:
        bust_uv_cache()
        if regenerate_uv_lock(repo_root, quiet=True):
            return True
        time.sleep(interval)
        # Exponential backoff: double interval up to max
        interval = min(interval * 2, max_interval)

    return False


def update_parent_dependency(parent_root: Path, package_name: str, new_version: str) -> bool:
    """Update a package dependency version in a parent project.

    Returns True if updated, False if no change needed.
    """
    pyproject = parent_root / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")

    # Match patterns like "package-name>=0.2.3" or 'package-name>=0.2.3'
    escaped_name = re.escape(package_name)
    new_content = re.sub(
        rf'(["\']){escaped_name}>=[\d.]+(["\'])',
        f"\\g<1>{package_name}>={new_version}\\g<2>",
        content,
    )

    if new_content != content:
        pyproject.write_text(new_content, encoding="utf-8")
        return True
    return False


class PublishRunner:
    """Handles publish workflow with dry-run support.

    Keeps dry-run and real execution in sync by using a single control flow.
    """

    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.step = 0

    def _step(self, description: str | None) -> None:
        """Print step description for dry-run or progress message.

        If description is None, the step is silent (used for sub-operations
        that are part of a larger logical step).
        """
        if description is None:
            return
        self.step += 1
        if self.dry_run:
            logger.info(f"  {self.step}. {description}")
        else:
            logger.next(description)

    def run_git(self, args: list[str], cwd: Path, description: str | None = None) -> None:
        """Run a git command, or print what would be done in dry-run mode.

        Pass description=None to run silently (as part of another step).
        """
        self._step(description)
        if not self.dry_run:
            run_cmd(["git"] + args, cwd=cwd, halt_on_fail=True)

    def run_shell(self, args: list[str], cwd: Path, description: str | None = None) -> bool:
        """Run a shell command, or print what would be done in dry-run mode.

        Pass description=None to run silently (as part of another step).
        Returns True on success, False on failure.
        """
        self._step(description)
        if not self.dry_run:
            result = run_cmd(args, cwd=cwd, halt_on_fail=False)
            return result.returncode == 0
        return True

    def action(self, description: str | None, func: Callable[[], object]) -> None:
        """Execute an action, or print what would be done in dry-run mode.

        Pass description=None to run silently (as part of another step).
        """
        self._step(description)
        if not self.dry_run:
            func()


@click.command()
@click.option(
    "--major",
    "part",
    flag_value="major",
    help="Bump major version (X.0.0)",
)
@click.option(
    "--minor",
    "part",
    flag_value="minor",
    help="Bump minor version (0.X.0)",
)
@click.option(
    "--patch",
    "part",
    flag_value="patch",
    default=True,
    help="Bump patch version (0.0.X) [default]",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
def publish(part: str, dry_run: bool):
    """Bump version and publish a Python package to PyPI.

    Reads the current version from pyproject.toml, bumps it according
    to the specified part (--major, --minor, or --patch), commits the
    change, creates a git tag, and pushes to trigger the publish workflow.

    If run from a parent project that depends on the published package,
    also updates the parent's dependency version and commits that change.

    If the parent project has the package in editable mode, this command will
    temporarily remove the editable configuration for the commit, then
    restore it afterward so local development can continue.

    \b
    SETUP REQUIREMENTS:

    1. GitHub Actions workflow (.github/workflows/publish.yaml):

       name: Publish to PyPI
       on:
         push:
           tags: ["v*.*.*"]
       permissions:
         contents: read
         id-token: write
       jobs:
         publish:
           runs-on: ubuntu-latest
           environment: pypi
           steps:
             - uses: actions/checkout@v4
             - uses: actions/setup-python@v5
               with:
                 python-version: "3.14"
             - run: pip install build && python -m build
             - uses: pypa/gh-action-pypi-publish@release/v1

    2. PyPI Trusted Publisher setup:
       - Go to pypi.org/manage/project/<package>/settings/publishing/
       - Add GitHub as trusted publisher:
         - Owner: <github-username>
         - Repository: <repo-name>
         - Workflow: publish.yaml
         - Environment: pypi

    3. GitHub Environment:
       - Create 'pypi' environment in repo Settings > Environments
       - No secrets needed (uses OIDC token)

    \b
    Examples:
        djb publish              # Bump patch: 0.2.0 -> 0.2.1
        djb publish --minor      # Bump minor: 0.2.0 -> 0.3.0
        djb publish --major      # Bump major: 0.2.0 -> 1.0.0
        djb publish --dry-run    # Show what would happen
    """
    # Discover package location
    # Try to get project_dir from config, but fall back to cwd for standalone packages
    try:
        project_root = config.project_dir
    except Exception:
        # Config not fully loaded (e.g., missing name/email for standalone package)
        project_root = Path.cwd()

    # First, check if we're in a host project with djb in editable mode
    # (this is the original djb-specific flow for backward compatibility)
    try:
        djb_source_path = get_djb_source_path(project_root)
    except Exception:
        djb_source_path = None

    if djb_source_path:
        # Host project with editable djb - publish djb
        package_root = (project_root / djb_source_path).resolve()
        parent_root = project_root
        package_name, current_version = get_package_info(package_root)
        logger.info(f"Found {package_name} at: {package_root}")
        logger.info(f"Found parent project at: {parent_root}")
    elif is_djb_package_dir(project_root) if project_root else False:
        # Running from djb directory - publish djb
        package_root = project_root.resolve()
        parent_root = None
        package_name, current_version = get_package_info(package_root)
        logger.info(f"Found {package_name} at: {package_root}")
    else:
        # Check if we're in any Python package directory
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                package_name, current_version = get_package_info(project_root)
                package_root = project_root.resolve()
                parent_root = None
                logger.info(f"Found {package_name} at: {package_root}")
            except click.ClickException:
                # Not a valid package, try fallback
                djb_dir = find_djb_dir(project_root)
                if djb_dir:
                    package_root = djb_dir.resolve()
                    parent_root = project_root
                    package_name, current_version = get_package_info(package_root)
                    logger.info(f"Found {package_name} at: {package_root}")
                    logger.info(f"Found parent project at: {parent_root}")
                else:
                    raise click.ClickException(
                        "Could not find a Python package to publish. "
                        "Run from a directory with pyproject.toml."
                    )
        else:
            # Fallback: look for djb/ subdirectory without editable config
            djb_dir = find_djb_dir(project_root)
            if djb_dir:
                package_root = djb_dir.resolve()
                parent_root = project_root
                package_name, current_version = get_package_info(package_root)
                logger.info(f"Found {package_name} at: {package_root}")
                logger.info(f"Found parent project at: {parent_root}")
            else:
                raise click.ClickException(
                    "Could not find a Python package to publish. "
                    "Run from a directory with pyproject.toml."
                )

    # Check if parent has the package in editable mode (only for djb currently)
    parent_editable = (
        parent_root is not None
        and package_name == "djb"
        and is_djb_editable(parent_root)
    )
    if parent_editable:
        logger.info(
            f"Parent project has {package_name} in editable mode "
            "(will be handled automatically)"
        )

    # Check if the package is a dependency of the parent project
    parent_has_dependency = (
        parent_root is not None and is_dependency_of(package_name, parent_root)
    )

    new_version = bump_version(current_version, part)
    tag_name = f"v{new_version}"

    logger.info(f"Package: {package_name}")
    logger.info(f"Current version: {current_version}")
    logger.info(f"New version: {new_version}")
    logger.info(f"Git tag: {tag_name}")

    if dry_run:
        logger.warning("[dry-run] Would perform the following:")

    runner = PublishRunner(dry_run)

    # Find version file for git add
    version_file = find_version_file(package_root, package_name)
    version_file_rel = version_file.relative_to(package_root) if version_file else None

    # Check for uncommitted changes (only in non-dry-run mode)
    if not dry_run:
        result = run_cmd(["git", "status", "--porcelain"], cwd=package_root, halt_on_fail=False)
        uncommitted = [
            line
            for line in result.stdout.strip().split("\n")
            if line
            and not line.endswith("pyproject.toml")
            and not line.endswith("_version.py")
        ]
        if uncommitted:
            logger.warning(f"You have uncommitted changes in {package_name}:")
            for line in uncommitted:
                logger.info(f"  {line}")
            if not click.confirm("Continue anyway?", default=False):
                raise click.ClickException("Aborted")
        logger.note()  # Blank line before steps

    # Phase 1: Update and publish the package
    runner.action(
        f"Update {package_name} version in pyproject.toml to {new_version}",
        lambda: set_version(package_root, package_name, new_version),
    )

    # Stage + commit as one logical step
    git_add_files = ["pyproject.toml"]
    if version_file_rel:
        git_add_files.append(str(version_file_rel))

    runner.run_git(["add"] + git_add_files, cwd=package_root)  # silent
    runner.run_git(
        ["commit", "-m", f"Bump {package_name} version to {new_version}"],
        cwd=package_root,
        description=f"Commit {package_name}: 'Bump {package_name} version to {new_version}'",
    )

    runner.run_git(
        ["tag", tag_name],
        cwd=package_root,
        description=f"Create tag: {tag_name}",
    )

    # Push commit + tag as one logical step
    runner.run_git(["push", "origin", "main"], cwd=package_root)  # silent
    runner.run_git(
        ["push", "origin", tag_name],
        cwd=package_root,
        description=f"Push {package_name} commit and tag to origin",
    )

    if not dry_run:
        logger.done(f"Published {package_name} {new_version}!")
        logger.info("The GitHub Actions workflow will build and upload to PyPI.")

    # Phase 2: Update parent project if it has this package as a dependency
    if parent_root and parent_has_dependency:
        if not dry_run:
            logger.next("Updating parent project dependency")

        # Stash editable config if active (only for djb currently)
        if parent_editable:
            runner.action(
                f"Stash editable {package_name} configuration",
                lambda: uninstall_editable_djb(parent_root, quiet=True),
            )

        try:
            runner.action(
                f"Update parent project dependency to {package_name}>={new_version}",
                lambda: update_parent_dependency(parent_root, package_name, new_version),
            )

            # Wait for uv to be able to resolve the new version
            # This retries uv lock until it succeeds (the actual source of truth)
            def wait_and_lock():
                logger.info(f"  Waiting for PyPI to have {package_name} available...")
                logger.info(
                    "  (This may take a few minutes while GitHub Actions builds and uploads)"
                )
                if not wait_for_uv_resolvable(parent_root, new_version):
                    # One final attempt with error output
                    if not regenerate_uv_lock(parent_root):
                        raise click.ClickException(
                            f"Timeout waiting for {package_name} {new_version} to be resolvable. "
                            "Try running: uv lock --refresh"
                        )

            runner.action("Regenerate uv.lock with new version", wait_and_lock)

            # Stage + commit as one step
            runner.run_git(["add", "pyproject.toml", "uv.lock"], cwd=parent_root)  # silent
            runner.run_git(
                ["commit", "-m", f"Update {package_name} dependency to {new_version}"],
                cwd=parent_root,
                description=f"Commit parent: 'Update {package_name} dependency to {new_version}'",
            )

            runner.run_git(
                ["push", "origin", "main"],
                cwd=parent_root,
                description="Push parent commit to origin",
            )

            if not dry_run:
                logger.done(
                    f"Updated parent project dependency to {package_name}>={new_version}"
                )

        finally:
            # Re-enable editable mode if it was active (even on error)
            if parent_editable:
                runner.action(
                    f"Re-enable editable {package_name} with current version",
                    lambda: restore_editable(parent_root, quiet=True),
                )
                if not dry_run:
                    logger.done("Editable mode restored for local development")
