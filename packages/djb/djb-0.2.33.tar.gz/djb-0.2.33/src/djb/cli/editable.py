"""
djb editable-djb CLI - Install/uninstall djb in editable mode.

Why This Command Exists
-----------------------
When developing djb alongside a project that uses it,
it's convenient to have djb installed in "editable" mode so that changes to
djb source code are immediately reflected without reinstalling.

Automatic Cloning
-----------------
If the djb directory doesn't exist when running `djb editable-djb`, the
command will automatically clone it from the canonical repository. You can
override the repository URL with --djb-repo and the target directory with
--djb-dir.

Why `uv add --editable` Instead of `uv pip install -e`
------------------------------------------------------
The key insight is that uv has TWO separate installation paths:

1. **uv pip install -e ./djb** - Installs directly into the virtual environment
   - Works immediately BUT gets overwritten by `uv sync` or `uv run`
   - uv sync reads pyproject.toml and reinstalls from PyPI, losing your edit

2. **uv add --editable ./djb** - Modifies pyproject.toml to track the source
   - Adds djb as a workspace member and source with editable=true
   - Now `uv sync` and `uv run` respect the editable installation
   - The editable mode persists across all uv commands

This is a common gotcha with uv. The direct pip install seems to work but
silently breaks when you run any other uv command. This command ensures you
always use the correct, persistent approach.

Deployment Consideration
------------------------
When deploying to Heroku (or any production environment), we must NOT have
djb in editable mode - the pyproject.toml must reference the PyPI version.
The `djb deploy heroku` command handles this automatically by stashing the
editable configuration during deployment. A pre-commit hook also warns if
you try to commit with editable mode enabled.

Usage:
    djb editable-djb              # Install djb in editable mode (clones if needed)
    djb editable-djb --status     # Check current mode
    djb editable-djb --uninstall  # Switch back to PyPI version
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import click
from packaging.requirements import Requirement

from djb.core.logging import get_logger
from djb.cli.utils import run_cmd

logger = get_logger(__name__)

# Canonical djb repository URL
DJB_REPO = "git@github.com:kajicom/djb.git"

# Default directory name for djb within a project
DJB_DEFAULT_DIR = "djb"

# Pre-commit hook content to prevent committing editable djb configuration
PRE_COMMIT_HOOK_CONTENT = """\
#!/bin/bash
# Pre-commit hook to prevent committing pyproject.toml with editable djb mode set.
# Installed by: djb editable-djb

set -e

# Check if pyproject.toml is being committed
if ! git diff --cached --name-only | grep -q "^pyproject.toml$"; then
    exit 0
fi

# Check if pyproject.toml contains editable djb configuration
if git show :pyproject.toml | grep -q 'editable = true'; then
    echo "ERROR: Cannot commit pyproject.toml with editable djb mode set."
    echo ""
    echo "The pyproject.toml file contains:"
    echo '  [tool.uv.sources]'
    echo '  djb = { workspace = true, editable = true }'
    echo ""
    echo "This is a development-only configuration that should not be committed."
    echo ""
    echo "To fix this, run:"
    echo "  djb editable-djb --uninstall"
    echo ""
    echo "This will switch djb back to the PyPI version for committing."
    echo "After committing, you can restore editable mode with:"
    echo "  djb editable-djb"
    exit 1
fi

# Check for orphaned workspace members (djb in members but no editable source)
PYPROJECT_CONTENT=$(git show :pyproject.toml)
if echo "$PYPROJECT_CONTENT" | grep -q '\\[tool\\.uv\\.workspace\\]' && \\
   echo "$PYPROJECT_CONTENT" | grep -q '"djb"'; then
    echo "ERROR: pyproject.toml has orphaned djb workspace member."
    echo ""
    echo "Found [tool.uv.workspace] with djb in members, but djb is not in editable mode."
    echo "This usually means 'djb editable-djb --uninstall' didn't complete cleanly."
    echo ""
    echo "To fix this, remove the [tool.uv.workspace] section from pyproject.toml:"
    echo '  [tool.uv.workspace]'
    echo '  members = ["djb"]'
    echo ""
    echo "Or run 'djb editable-djb --uninstall' again to attempt automatic cleanup."
    exit 1
fi

# Also check uv.lock for editable references
if git diff --cached --name-only | grep -q "^uv.lock$"; then
    if git show :uv.lock 2>/dev/null | grep -q "editable = true"; then
        echo "ERROR: Cannot commit uv.lock with editable djb references."
        echo ""
        echo "Run 'djb editable-djb --uninstall' to switch to PyPI version first."
        exit 1
    fi
fi

exit 0
"""


def get_djb_version_specifier(repo_root: Path) -> str | None:
    """Get the djb version specifier from pyproject.toml dependencies.

    Uses proper TOML parsing and packaging.requirements.Requirement
    to handle all PEP 508 version specifiers (>=, ==, ~=, <, etc.),
    extras syntax, and environment markers.

    Returns the version specifier (e.g., ">=0.2.6") or None if not found.
    """
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError:
        return None

    # Collect all dependencies from both regular and optional dependencies
    all_deps: list[str] = []
    if "project" in data:
        if "dependencies" in data["project"]:
            deps = data["project"]["dependencies"]
            if isinstance(deps, list):
                all_deps.extend(deps)
        if "optional-dependencies" in data["project"]:
            for group_deps in data["project"]["optional-dependencies"].values():
                if isinstance(group_deps, list):
                    all_deps.extend(group_deps)

    # Use packaging.requirements.Requirement to properly parse each dependency
    for dep in all_deps:
        try:
            req = Requirement(dep)
            if req.name == "djb":
                # Return the specifier string (e.g., ">=0.2.6" or ">=0.2.6,<1.0")
                specifier_str = str(req.specifier)
                return specifier_str if specifier_str else None
        except Exception:
            # Skip malformed dependency strings
            continue

    return None


def is_djb_package_dir(path: Path) -> bool:
    """Check if the given path is the djb package directory.

    Uses proper TOML parsing to check if pyproject.toml has name = "djb".
    """
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return False

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("name") == "djb"
    except (OSError, tomllib.TOMLDecodeError):
        return False


def find_djb_dir(
    repo_root: Path | None = None,
    *,
    raise_on_missing: bool = False,
) -> Path | None:
    """Find the djb directory relative to repo_root or cwd.

    Args:
        repo_root: Directory to search from. Defaults to cwd.
        raise_on_missing: If True, raise ClickException when not found.

    Returns:
        Path to the djb directory, or None if not found (and raise_on_missing=False).

    Raises:
        click.ClickException: If not found and raise_on_missing=True.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    # Check if djb/ exists in the directory
    if (repo_root / "djb" / "pyproject.toml").exists():
        return repo_root / "djb"

    # Check if we're inside the djb directory
    if is_djb_package_dir(repo_root):
        return repo_root

    if raise_on_missing:
        raise click.ClickException(
            "Could not find djb package. Run from djb directory or a parent containing djb/"
        )

    return None


def _get_djb_source_config(pyproject_path: Path) -> dict | None:
    """Get the djb source configuration from pyproject.toml.

    Reads [tool.uv.sources.djb] from pyproject.toml if present.

    Returns:
        The djb source dict if configured, None otherwise.
    """
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return None

    tool = data.get("tool", {})
    uv = tool.get("uv", {})
    sources = uv.get("sources", {})
    return sources.get("djb")


def is_djb_editable(repo_root: Path | None = None) -> bool:
    """Check if djb is currently installed in editable mode via pyproject.toml.

    This checks for a [tool.uv.sources] entry for djb with editable=true.
    """
    if repo_root is None:
        repo_root = Path.cwd()
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    djb_config = _get_djb_source_config(pyproject_path)
    if djb_config is None:
        return False
    return djb_config.get("editable", False)


def _get_workspace_members(pyproject_path: Path) -> list[str]:
    """Get the workspace members from pyproject.toml.

    Reads [tool.uv.workspace.members] from pyproject.toml if present.

    Returns:
        List of workspace member paths, or empty list if not configured.
    """
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return []

    tool = data.get("tool", {})
    uv = tool.get("uv", {})
    workspace = uv.get("workspace", {})
    return workspace.get("members", [])


def get_djb_source_path(repo_root: Path | None = None) -> str | None:
    """Get the path to the editable djb source if installed in editable mode.

    Expects workspace configuration:
    - [tool.uv.sources] djb = { workspace = true, editable = true }
    - [tool.uv.workspace] members = ["djb"]

    Looks up djb in workspace members to find the path.
    """
    if repo_root is None:
        repo_root = Path.cwd()
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    djb_config = _get_djb_source_config(pyproject_path)
    if djb_config is None or not djb_config.get("editable"):
        return None

    # Check for workspace configuration
    if djb_config.get("workspace"):
        # Look for djb in workspace members
        members = _get_workspace_members(pyproject_path)
        for member in members:
            # Member could be "djb" or "packages/djb" etc.
            member_path = repo_root / member
            if is_djb_package_dir(member_path):
                return member

    return None


def get_installed_djb_version(repo_root: Path | None = None) -> str | None:
    """Get the currently installed djb version."""
    if repo_root is None:
        repo_root = Path.cwd()

    result = run_cmd(["uv", "pip", "show", "djb"], cwd=repo_root, halt_on_fail=False)
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return None


def _install_pre_commit_hook(repo_root: Path, quiet: bool = False) -> bool:
    """Install or update the pre-commit hook to prevent committing editable config.

    Args:
        repo_root: Project root directory
        quiet: If True, suppress output messages

    Returns:
        True if hook was installed/updated, False if not in a git repo
    """
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        return False  # Not a git repo

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    hook_path = hooks_dir / "pre-commit"

    # Check if hook already exists and has same content
    if hook_path.exists():
        try:
            existing_content = hook_path.read_text()
            if existing_content == PRE_COMMIT_HOOK_CONTENT:
                return True  # Already up to date
        except OSError:
            pass

    try:
        hook_path.write_text(PRE_COMMIT_HOOK_CONTENT)
        hook_path.chmod(0o755)  # Make executable
        if not quiet:
            if hook_path.exists():
                logger.info("Updated pre-commit hook to prevent committing editable config")
            else:
                logger.info("Installed pre-commit hook to prevent committing editable config")
        return True
    except OSError:
        if not quiet:
            logger.warning("Could not install pre-commit hook")
        return False


def _remove_djb_workspace_member(pyproject_path: Path, quiet: bool = False) -> bool:
    """Remove djb from workspace members in pyproject.toml.

    This cleans up the [tool.uv.workspace] section after uv remove, which
    doesn't remove workspace members automatically.

    Args:
        pyproject_path: Path to pyproject.toml
        quiet: If True, suppress warning messages

    Returns:
        True if cleanup was successful or not needed, False on error
    """
    if not pyproject_path.exists():
        return True

    try:
        content = pyproject_path.read_text()
    except OSError:
        return False

    # Check if there's a workspace section with djb as a member
    if "[tool.uv.workspace]" not in content or '"djb"' not in content:
        return True  # Nothing to clean up

    # Pattern to match the entire [tool.uv.workspace] section with only djb as member
    # This handles the common case where djb is the only workspace member
    pattern = r'\[tool\.uv\.workspace\]\s*\nmembers\s*=\s*\[\s*\n?\s*"djb",?\s*\n?\s*\]\s*\n?'

    new_content, count = re.subn(pattern, "", content)

    if count == 0:
        # Pattern didn't match - might have other members or unusual formatting
        if not quiet:
            logger.warning(
                "Could not automatically clean up [tool.uv.workspace] section. "
                "Please manually remove 'djb' from workspace members in pyproject.toml"
            )
        return True  # Not a fatal error, just a warning

    try:
        pyproject_path.write_text(new_content)
        return True
    except OSError:
        return False


def _remove_djb_source_entry(pyproject_path: Path, quiet: bool = False) -> bool:
    """Remove djb from [tool.uv.sources] in pyproject.toml.

    This cleans up any leftover djb source entry (workspace or path-based).

    Args:
        pyproject_path: Path to pyproject.toml
        quiet: If True, suppress warning messages

    Returns:
        True if cleanup was successful or not needed, False on error
    """
    if not pyproject_path.exists():
        return True

    try:
        content = pyproject_path.read_text()
    except OSError:
        return False

    # Check if there's a sources section with djb
    if "[tool.uv.sources]" not in content:
        return True  # Nothing to clean up

    # Pattern to match djb entry in sources (handles both workspace and path formats)
    # Matches: djb = { workspace = true } or djb = { workspace = true, editable = true }
    # or djb = { path = "djb", editable = true }
    djb_source_pattern = r"djb\s*=\s*\{[^}]+\}\s*\n?"

    new_content, count = re.subn(djb_source_pattern, "", content)

    if count == 0:
        return True  # No djb entry found

    # If [tool.uv.sources] section is now empty, remove it entirely
    empty_sources_pattern = r"\[tool\.uv\.sources\]\s*\n(?=\[|\Z)"
    new_content = re.sub(empty_sources_pattern, "", new_content)

    try:
        pyproject_path.write_text(new_content)
        return True
    except OSError:
        return False


def uninstall_editable_djb(repo_root: Path | None = None, quiet: bool = False) -> bool:
    """Uninstall editable djb and reinstall from PyPI.

    Args:
        repo_root: Project root directory (default: cwd)
        quiet: If True, suppress output messages

    Returns:
        True on success, False on failure
    """
    if repo_root is None:
        repo_root = Path.cwd()

    # Save the version specifier BEFORE removing (uv remove will delete it)
    version_specifier = get_djb_version_specifier(repo_root)

    result = run_cmd(
        ["uv", "remove", "djb"],
        cwd=repo_root,
        halt_on_fail=False,
        label="Removing editable djb",
        fail_msg="Failed to remove djb",
        quiet=quiet,
    )
    if result.returncode != 0:
        return False

    # Clean up workspace members and source entries BEFORE re-adding djb.
    # If we don't, uv add will see the workspace member and automatically
    # add djb = { workspace = true } to [tool.uv.sources].
    pyproject_path = repo_root / "pyproject.toml"
    _remove_djb_workspace_member(pyproject_path, quiet=quiet)
    _remove_djb_source_entry(pyproject_path, quiet=quiet)

    # Re-add with the original version specifier to preserve it
    # Use --refresh to bypass uv's resolver cache and get the latest from PyPI
    djb_spec = f"djb{version_specifier}" if version_specifier else "djb"
    result = run_cmd(
        ["uv", "add", "--refresh", djb_spec],
        cwd=repo_root,
        halt_on_fail=False,
        label="Re-adding djb from PyPI",
        fail_msg="Failed to add djb from PyPI",
        quiet=quiet,
    )
    if result.returncode != 0:
        return False

    if not quiet:
        version = get_installed_djb_version(repo_root)
        version_str = f" (v{version})" if version else ""
        logger.done(f"Switched to PyPI version of djb{version_str}")
    return True


def clone_djb_repo(
    djb_dir: Path,
    djb_repo: str = DJB_REPO,
    quiet: bool = False,
) -> bool:
    """Clone the djb repository to the specified directory.

    Args:
        djb_dir: Target directory for the clone
        djb_repo: Git repository URL to clone from
        quiet: If True, suppress output messages

    Returns:
        True on success, False on failure
    """
    result = run_cmd(
        ["git", "clone", djb_repo, str(djb_dir)],
        halt_on_fail=False,
        label=f"Cloning djb repository from '{djb_repo}' into '{djb_dir}'",
        done_msg="djb repository cloned",
        fail_msg="Failed to clone djb repository",
        quiet=quiet,
    )
    return result.returncode == 0


def install_editable_djb(
    repo_root: Path | None = None,
    quiet: bool = False,
    djb_repo: str = DJB_REPO,
    djb_dir: str = DJB_DEFAULT_DIR,
) -> bool:
    """Install djb in editable mode from local directory.

    Uses `uv add --editable` which modifies pyproject.toml to track the
    editable source, ensuring it persists across `uv sync` operations.

    If the djb directory doesn't exist, it will be cloned from djb_repo.

    Args:
        repo_root: Project root directory (default: cwd)
        quiet: If True, suppress output messages
        djb_repo: Git repository URL to clone from if djb directory doesn't exist
        djb_dir: Directory name for djb within the project

    Returns:
        True on success, False on failure
    """
    if repo_root is None:
        repo_root = Path.cwd()

    djb_path = find_djb_dir(repo_root)

    # If djb directory not found, try to clone it
    if not djb_path:
        target_dir = repo_root / djb_dir
        if not quiet:
            logger.info(f"djb directory not found, cloning from {djb_repo}...")
        if not clone_djb_repo(target_dir, djb_repo, quiet):
            return False
        djb_path = target_dir

    result = run_cmd(
        ["uv", "add", "--editable", str(djb_path)],
        cwd=repo_root,
        halt_on_fail=False,
        label=f"Installing djb in editable mode from {djb_path}",
        fail_msg="Failed to add editable djb",
        quiet=quiet,
    )
    if result.returncode != 0:
        return False

    # Install pre-commit hook to prevent accidental commits
    _install_pre_commit_hook(repo_root, quiet=quiet)

    if not quiet:
        version = get_installed_djb_version(repo_root)
        version_str = f" (v{version})" if version else ""
        logger.done(f"djb installed in editable mode{version_str}")
        logger.info(f"  Source: {djb_path}")
    return True


def show_status(repo_root: Path | None = None) -> None:
    """Show the current djb installation status."""
    if repo_root is None:
        repo_root = Path.cwd()

    version = get_installed_djb_version(repo_root)
    is_editable = is_djb_editable(repo_root)
    source_path = get_djb_source_path(repo_root)

    logger.info("djb installation status:")
    logger.note()

    if version:
        logger.info(f"  Version: {version}")
    else:
        logger.warning("  Not installed")
        return

    if is_editable:
        logger.done("  Mode: editable (local development)")
        if source_path:
            logger.info(f"  Source: {source_path}")
    else:
        logger.info("  Mode: PyPI (production)")

    logger.note()

    if is_editable:
        logger.info("To switch to PyPI version:")
        logger.tip("  djb editable-djb --uninstall")
    else:
        djb_dir = find_djb_dir(repo_root)
        if djb_dir:
            logger.info("To switch to editable mode:")
            logger.tip("  djb editable-djb")
        else:
            logger.info("No local djb directory found.")
            logger.info("To clone and install in editable mode:")
            logger.tip("  djb editable-djb")


@click.command("editable-djb")
@click.option(
    "--uninstall",
    is_flag=True,
    help="Uninstall editable djb and use PyPI version instead.",
)
@click.option(
    "--status",
    is_flag=True,
    help="Show current djb installation status.",
)
@click.option(
    "--djb-repo",
    default=DJB_REPO,
    show_default=True,
    help="Git repository URL to clone djb from if not already present.",
)
@click.option(
    "--djb-dir",
    default=DJB_DEFAULT_DIR,
    show_default=True,
    help="Directory name for djb within the project.",
)
def editable_djb(uninstall: bool, status: bool, djb_repo: str, djb_dir: str):
    """Install or uninstall djb in editable mode.

    Uses `uv add --editable` which modifies pyproject.toml to add a
    [tool.uv.sources] section. This ensures that `uv sync` and `uv run`
    respect the editable installation.

    If the djb directory doesn't exist, it will be cloned from --djb-repo.

    IMPORTANT: Never use `uv pip install -e ./djb` directly - it will be
    overwritten by `uv sync`. Always use this command instead.

    \b
    Examples:
        djb editable-djb              # Install editable djb (clones if needed)
        djb editable-djb --status     # Check current status
        djb editable-djb --uninstall  # Switch back to PyPI version
    """
    if status:
        show_status()
        return

    if uninstall:
        if not is_djb_editable():
            logger.info("djb is not currently in editable mode.")
            return
        if not uninstall_editable_djb():
            raise click.ClickException("Failed to uninstall editable djb")
    else:
        if is_djb_editable():
            source_path = get_djb_source_path()
            logger.info(f"djb is already installed in editable mode from {source_path}")
            logger.tip("Use --uninstall to switch back to PyPI version.")
            return
        if not install_editable_djb(djb_repo=djb_repo, djb_dir=djb_dir):
            raise click.ClickException("Failed to install editable djb")
