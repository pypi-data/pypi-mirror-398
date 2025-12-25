"""
djb init CLI - Initialize djb development environment.

Provides commands for setting up system dependencies, Python packages, and frontend tooling.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import click

from djb import config
from djb.cli.db import init_database
from djb.core.logging import get_logger
from djb.cli.secrets import _ensure_prerequisites as ensure_secrets_prerequisites
from djb.cli.seed import run_seed_command
from djb.cli.utils import check_cmd, run_cmd
from djb.config import LOCAL, PROJECT, get_config_path
from djb.config.acquisition import GitConfigSource, acquire_all_fields
from djb.secrets import init_gpg_agent_config, init_or_upgrade_secrets

logger = get_logger(__name__)


def _get_clipboard_command() -> str:
    """Get the appropriate clipboard command for the current platform.

    Returns:
        'clip.exe' on WSL2, 'pbcopy' on macOS, 'xclip' on Linux.
    """
    # Check for WSL2 first
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                return "clip.exe"
    except (FileNotFoundError, PermissionError):
        pass

    # macOS
    if sys.platform == "darwin":
        return "pbcopy"

    # Linux fallback
    return "xclip"


def _set_git_config(key: str, value: str) -> bool:
    """Set a value in git config (global)."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", key, value],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def _configure_all_fields(project_dir: Path) -> dict[str, Any]:
    """Configure all config fields using the acquisition generator.

    Field order is determined by declaration order in DjbConfig.
    Acquirable fields are those with an acquire() method and prompt_text.

    Args:
        project_dir: Project root directory.

    Returns:
        Dict of configured field values.
    """
    configured: dict[str, Any] = {}
    copied_from_git: list[str] = []

    logger.next("Configuring project settings")

    for field_name, result in acquire_all_fields(project_dir, config):
        configured[field_name] = result.value

        # Track git config sources for summary message
        if result.source_name == "git config":
            copied_from_git.append(field_name)

    # Summary message for git config copies
    if copied_from_git:
        logger.info(f"Copied {' and '.join(copied_from_git)} from git config")

    # Log config file location
    config_path = get_config_path(LOCAL, project_dir)
    if any(f in configured for f in ("name", "email")):
        logger.info(f"Config saved to: {config_path}")

    return configured


def _sync_identity_to_git() -> None:
    """Sync name/email from djb config to git global config if needed.

    If name/email are in djb config but not from git config, sync them
    so users don't have to configure git separately.
    """
    for field_name in ("name", "email"):
        source = config.get_source(field_name)
        value = getattr(config, field_name, None)

        # Only sync if we have a value from djb config (not from git)
        if value and source is not None and source.is_explicit():
            git_key = "user.name" if field_name == "name" else "user.email"
            git_source = GitConfigSource(git_key)
            # Only sync if git config doesn't already have this value
            if git_source.get() != value:
                _set_git_config(git_key, value)


def _find_settings_file(project_root: Path) -> Path | None:
    """Find the Django settings.py file in the project.

    Searches for settings.py in subdirectories of project_root that look like
    Django project directories (contain __init__.py).

    Returns:
        Path to settings.py if found, None otherwise.
    """
    # Look for directories containing settings.py
    for item in project_root.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            settings_path = item / "settings.py"
            init_path = item / "__init__.py"
            # Must have both settings.py and __init__.py to be a Django project
            if settings_path.exists() and init_path.exists():
                return settings_path
    return None


def _add_djb_to_installed_apps(project_root: Path) -> bool:
    """Add 'djb' to Django's INSTALLED_APPS if not already present.

    Finds the settings.py file and modifies INSTALLED_APPS to include 'djb'.
    Inserts djb after the last django.* app for proper ordering.

    Returns:
        True if djb was added, False if already present or settings not found.
    """
    logger.next("Configuring Django settings")
    settings_path = _find_settings_file(project_root)
    if not settings_path:
        logger.skip("No Django settings.py found")
        return False

    content = settings_path.read_text()

    # Check if djb is already in INSTALLED_APPS
    # Match various formats: "djb", 'djb', with or without trailing comma
    if re.search(r'["\']djb["\']', content):
        logger.done("djb already in INSTALLED_APPS")
        return False

    # Find INSTALLED_APPS list and insert djb
    # Match the pattern: INSTALLED_APPS = [
    pattern = r"(INSTALLED_APPS\s*=\s*\[)"

    match = re.search(pattern, content)
    if not match:
        logger.warning("Could not find INSTALLED_APPS in settings.py")
        return False

    # Find a good insertion point - after the last django.* entry
    # or at the end of the list if no django entries
    lines = content.split("\n")
    installed_apps_start = None
    last_django_line = None
    bracket_depth = 0
    in_installed_apps = False

    for i, line in enumerate(lines):
        if "INSTALLED_APPS" in line and "=" in line:
            installed_apps_start = i
            in_installed_apps = True

        if in_installed_apps:
            bracket_depth += line.count("[") - line.count("]")
            # Match django.* apps (django.contrib.*, django_components, etc.)
            if re.search(r'["\']django[._]', line):
                last_django_line = i
            if bracket_depth == 0 and installed_apps_start is not None and i > installed_apps_start:
                break

    if last_django_line is not None:
        # Insert after the last django.* line
        insert_line = last_django_line
        # Detect indentation from the previous line
        indent_match = re.match(r"^(\s*)", lines[insert_line])
        indent = indent_match.group(1) if indent_match else "    "
        lines.insert(insert_line + 1, f'{indent}"djb",')
    elif installed_apps_start is not None:
        # No django entries, insert after the opening bracket
        indent = "    "
        lines.insert(installed_apps_start + 1, f'{indent}"djb",')
    else:
        logger.warning("Could not determine where to insert djb in INSTALLED_APPS")
        return False

    # Write the modified content
    settings_path.write_text("\n".join(lines))
    logger.done(f"Added djb to INSTALLED_APPS in {settings_path.name}")
    return True


def _update_gitignore_for_project_config(project_root: Path) -> bool:
    """Update .gitignore to ensure .djb/local.yaml is ignored.

    Adds '.djb/local.yaml' if not already present.

    Returns:
        True if .gitignore was updated, False otherwise.
    """
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return False

    content = gitignore_path.read_text()

    # Already has the correct entry
    if ".djb/local.yaml" in content:
        return False

    # Add .djb/local.yaml
    entry = "\n# djb local config (user-specific, not committed)\n.djb/local.yaml\n"
    gitignore_path.write_text(content.rstrip() + entry)
    return True


def _install_git_hooks(project_root: Path, *, skip: bool = False) -> None:
    """Install git hooks for the project.

    Installs:
    - pre-commit hook to prevent committing pyproject.toml with editable djb

    Args:
        project_root: Path to project root.
        skip: If True, skip hook installation entirely.
    """
    if skip:
        logger.skip("Git hooks installation")
        return

    logger.next("Installing git hooks")

    git_dir = project_root / ".git"
    if not git_dir.exists():
        logger.skip("Not a git repository, skipping hooks")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Source hook script location
    hook_source = project_root / "scripts" / "pre-commit-editable-check"

    if not hook_source.exists():
        logger.warning(f"Hook script not found at {hook_source}")
        logger.info("  Create scripts/pre-commit-editable-check to enable hook installation")
        return

    # Destination hook path
    pre_commit_hook = hooks_dir / "pre-commit"

    # Check if pre-commit hook already exists
    if pre_commit_hook.exists():
        # Check if it's our hook or something else
        content = pre_commit_hook.read_text()
        if "pre-commit-editable-check" in content or "editable djb" in content:
            logger.done("Git hooks already installed")
            return
        else:
            # There's an existing pre-commit hook, don't overwrite it
            logger.warning("Existing pre-commit hook found, not overwriting")
            logger.info(f"  To install manually, add a call to: {hook_source}")
            return

    # Install the hook by copying the script
    shutil.copy(hook_source, pre_commit_hook)
    pre_commit_hook.chmod(0o755)
    logger.done("Git hooks installed (pre-commit: editable djb check)")


# =============================================================================
# Init step functions - each handles one phase of initialization
# =============================================================================


def _validate_project(project_root: Path) -> None:
    """Validate we're in a Python project with pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        raise click.ClickException(
            f"No pyproject.toml found in {project_root}. "
            "Run 'djb init' from your project root directory."
        )


def _install_brew_dependencies(*, skip: bool = False) -> None:
    """Install system dependencies via Homebrew.

    Args:
        skip: If True, skip installation entirely.
    """
    is_brew_supported = sys.platform in ("darwin", "linux")

    if skip:
        logger.skip("System dependency installation")
        return

    if not is_brew_supported:
        logger.skip("Homebrew installation (not supported on this platform)")
        logger.info("Please install dependencies manually:")
        logger.info("  - SOPS: https://github.com/getsops/sops")
        logger.info("  - age: https://age-encryption.org/")
        logger.info("  - GnuPG: https://gnupg.org/")
        logger.info("  - PostgreSQL 17: https://www.postgresql.org/")
        logger.info("  - GDAL: https://gdal.org/")
        logger.info("  - Bun: https://bun.sh/")
        return

    logger.next("Installing system dependencies via Homebrew")

    if not check_cmd(["which", "brew"]):
        logger.error("Homebrew not found. Please install from https://brew.sh/")
        raise click.ClickException("Homebrew is required for automatic dependency installation")

    # Install SOPS (for secrets encryption)
    if not check_cmd(["brew", "list", "sops"]):
        run_cmd(["brew", "install", "sops"], label="Installing sops", done_msg="sops installed")
    else:
        logger.done("sops already installed")

    # Install age (for secrets encryption)
    if not check_cmd(["brew", "list", "age"]):
        run_cmd(["brew", "install", "age"], label="Installing age", done_msg="age installed")
    else:
        logger.done("age already installed")

    # Install GnuPG (for age key encryption)
    if not check_cmd(["brew", "list", "gnupg"]):
        run_cmd(
            ["brew", "install", "gnupg"],
            label="Installing gnupg",
            done_msg="gnupg installed",
        )
    else:
        logger.done("gnupg already installed")

    # Install PostgreSQL (for database)
    if not check_cmd(["brew", "list", "postgresql@17"]):
        run_cmd(
            ["brew", "install", "postgresql@17"],
            label="Installing PostgreSQL",
            done_msg="postgresql@17 installed",
        )
    else:
        logger.done("postgresql@17 already installed")

    # Install GDAL (for GeoDjango)
    if not check_cmd(["brew", "list", "gdal"]):
        run_cmd(["brew", "install", "gdal"], label="Installing GDAL", done_msg="gdal installed")
    else:
        logger.done("gdal already installed")

    # Install Bun (JavaScript runtime)
    if not check_cmd(["which", "bun"]):
        run_cmd(
            ["brew", "install", "oven-sh/bun/bun"],
            label="Installing Bun",
            done_msg="bun installed",
        )
    else:
        logger.done("bun already installed")

    logger.done("System dependencies ready")


def _install_python_dependencies(project_root: Path, *, skip: bool = False) -> None:
    """Install Python dependencies via uv.

    Args:
        project_root: Path to project root.
        skip: If True, skip installation entirely.
    """
    if skip:
        logger.skip("Python dependency installation")
        return

    run_cmd(
        ["uv", "sync", "--upgrade-package", "djb"],
        cwd=project_root,
        label="Installing Python dependencies (and upgrading djb to latest)",
        done_msg="Python dependencies installed",
    )


def _install_frontend_dependencies(project_root: Path, *, skip: bool = False) -> None:
    """Install frontend dependencies via bun.

    Args:
        project_root: Path to project root.
        skip: If True, skip installation entirely.
    """
    if skip:
        logger.skip("Frontend dependency installation")
        return

    frontend_dir = project_root / "frontend"
    if frontend_dir.exists():
        run_cmd(
            ["bun", "install"],
            cwd=frontend_dir,
            label="Installing frontend dependencies",
            done_msg="Frontend dependencies installed",
        )
    else:
        logger.skip(f"Frontend directory not found at {frontend_dir}")


def _init_database(project_root: Path, *, skip: bool = False) -> bool:
    """Initialize the development database.

    Args:
        project_root: Path to project root.
        skip: If True, skip database initialization entirely.

    Returns:
        True if database was initialized or skipped, False if failed.
    """
    if skip:
        logger.skip("Database initialization")
        return True

    logger.next("Initializing development database")
    if not init_database(start_service=True, quiet=False):
        logger.warning("Database initialization failed - you can run 'djb db init' later")
        return False
    return True


def _run_migrations(project_root: Path, *, skip: bool = False) -> bool:
    """Run Django migrations.

    Args:
        project_root: Path to project root.
        skip: If True, skip migrations entirely.

    Returns:
        True if migrations succeeded or skipped, False if failed.
    """
    if skip:
        logger.skip("Django migrations")
        return True

    logger.next("Running Django migrations")
    result = run_cmd(
        ["uv", "run", "python", "manage.py", "migrate"],
        cwd=project_root,
        label="Running migrations",
        done_msg="Migrations complete",
        halt_on_fail=False,
    )
    if result.returncode != 0:
        logger.warning("Migrations failed - you can run 'python manage.py migrate' later")
        return False
    return True


def _run_seed(*, skip: bool = False) -> bool:
    """Run the host project's seed command if configured.

    Args:
        skip: If True, skip seeding entirely.

    Returns:
        True if seed succeeded, skipped, or not configured, False if failed.
    """
    if skip:
        logger.skip("Database seeding")
        return True

    if not config.seed_command:
        logger.skip("No seed_command configured")
        return True

    logger.next("Seeding database")
    if not run_seed_command(config):
        logger.warning("Seed failed - you can run 'djb seed' later")
        return False
    logger.done("Database seeded")
    return True


def _init_secrets(
    project_root: Path,
    user_email: str | None,
    user_name: str | None,
    project_name: str,
    *,
    skip: bool = False,
) -> None:
    """Initialize secrets management.

    Args:
        project_root: Path to project root.
        user_email: User email for secrets.
        user_name: User name for secrets.
        project_name: Project name for secrets.
        skip: If True, skip secrets initialization entirely.
    """
    if skip:
        logger.skip("Secrets initialization")
        return

    logger.next("Initializing secrets management")

    if not ensure_secrets_prerequisites(quiet=True):
        raise click.ClickException("Cannot initialize secrets without SOPS and age")

    if init_gpg_agent_config():
        logger.done("Created GPG agent config with passphrase caching")

    status = init_or_upgrade_secrets(
        project_root, email=user_email, name=user_name, project_name=project_name
    )

    if status.initialized:
        logger.done(f"Created secrets: {', '.join(status.initialized)}")
    if status.upgraded:
        logger.done(f"Upgraded secrets: {', '.join(status.upgraded)}")
    if status.up_to_date and not status.initialized and not status.upgraded:
        logger.done("Secrets already up to date")

    # Auto-commit .sops.yaml if this is a git repo and the file was modified
    _auto_commit_secrets(project_root, user_email)


def _auto_commit_secrets(project_root: Path, user_email: str | None) -> None:
    """Auto-commit secrets config to git if modified."""
    secrets_dir = project_root / "secrets"
    git_dir = project_root / ".git"

    if not git_dir.exists() or not user_email:
        return

    sops_config = secrets_dir / ".sops.yaml"
    files_to_commit = []

    if sops_config.exists():
        result = run_cmd(
            ["git", "status", "--porcelain", str(sops_config)],
            cwd=project_root,
            halt_on_fail=False,
        )
        if result.stdout.strip():
            files_to_commit.append(str(sops_config.relative_to(project_root)))

    if files_to_commit:
        logger.next("Committing public key to git")
        logger.info(f"Files: {', '.join(files_to_commit)}")

        for file in files_to_commit:
            run_cmd(["git", "add", file], cwd=project_root, halt_on_fail=False)

        commit_msg = f"Add public key for {user_email}"
        result = run_cmd(
            ["git", "commit", "-m", commit_msg],
            cwd=project_root,
            halt_on_fail=False,
            fail_msg="Could not commit public key",
        )
        if result.returncode == 0:
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    logger.info(f"  {line}")
            logger.done("Public key committed")


def _auto_commit_project_config(project_root: Path, gitignore_updated: bool) -> None:
    """Auto-commit project config files to git if modified."""
    git_dir = project_root / ".git"
    if not git_dir.exists():
        return

    project_config_path = get_config_path(PROJECT, project_root)
    gitignore_path = project_root / ".gitignore"

    config_files_to_commit = []

    if project_config_path.exists():
        result = run_cmd(
            ["git", "status", "--porcelain", str(project_config_path)],
            cwd=project_root,
            halt_on_fail=False,
        )
        if result.stdout.strip():
            config_files_to_commit.append(str(project_config_path.relative_to(project_root)))

    if gitignore_updated:
        result = run_cmd(
            ["git", "status", "--porcelain", str(gitignore_path)],
            cwd=project_root,
            halt_on_fail=False,
        )
        if result.stdout.strip():
            config_files_to_commit.append(".gitignore")

    if config_files_to_commit:
        logger.next("Committing project config to git")
        logger.info(f"Files: {', '.join(config_files_to_commit)}")

        for file in config_files_to_commit:
            run_cmd(["git", "add", file], cwd=project_root, halt_on_fail=False)

        commit_msg = "Add djb project config"
        result = run_cmd(
            ["git", "commit", "-m", commit_msg],
            cwd=project_root,
            halt_on_fail=False,
            fail_msg="Could not commit project config",
        )
        if result.returncode == 0:
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    logger.info(f"  {line}")
            logger.done("Project config committed")


def _show_success_message() -> None:
    """Show final success message with next steps."""
    logger.done("djb initialization complete!")
    logger.note()
    logger.info("To start developing, run in separate terminals:")
    logger.info("  1. python manage.py runserver")
    logger.info("  2. cd frontend && bun run dev")
    logger.note()
    clip_cmd = _get_clipboard_command()
    logger.tip(f"Back up your private secrets Age key: djb secrets export-key | {clip_cmd}")
    logger.tip(
        "Push your commit, then ask a teammate to run: djb secrets rotate\n"
        "         (This gives you access to staging/production secrets)"
    )


@click.command("init")
@click.option(
    "--skip-brew",
    is_flag=True,
    help="Skip installing system dependencies via Homebrew",
)
@click.option(
    "--skip-python",
    is_flag=True,
    help="Skip installing Python dependencies",
)
@click.option(
    "--skip-frontend",
    is_flag=True,
    help="Skip installing frontend dependencies",
)
@click.option(
    "--skip-db",
    is_flag=True,
    help="Skip database initialization",
)
@click.option(
    "--skip-migrations",
    is_flag=True,
    help="Skip running Django migrations",
)
@click.option(
    "--skip-seed",
    is_flag=True,
    help="Skip running the seed command",
)
@click.option(
    "--skip-secrets",
    is_flag=True,
    help="Skip secrets initialization",
)
@click.option(
    "--skip-hooks",
    is_flag=True,
    help="Skip installing git hooks",
)
def init(
    skip_brew: bool,
    skip_python: bool,
    skip_frontend: bool,
    skip_db: bool,
    skip_migrations: bool,
    skip_seed: bool,
    skip_secrets: bool,
    skip_hooks: bool,
):
    """Initialize djb development environment.

    Sets up everything needed for local development:

    \b
    * System dependencies (Homebrew): SOPS, age, PostgreSQL, GDAL, Bun
    * Python dependencies: uv sync
    * Django settings: adds djb to INSTALLED_APPS
    * Frontend dependencies: bun install in frontend/
    * Database: creates PostgreSQL database and user
    * Django migrations: runs migrate command
    * Database seeding: runs seed command (if configured)
    * Git hooks: pre-commit hook to prevent committing editable djb
    * Secrets management: SOPS-encrypted configuration

    This command is idempotent - safe to run multiple times.
    Already-installed dependencies are skipped automatically.

    \b
    Examples:
      djb init                    # Full setup
      djb init --skip-brew        # Skip Homebrew (already installed)
      djb init --skip-db          # Skip database (configure later)
      djb init --skip-secrets     # Skip secrets (configure later)
    """
    project_dir = config.project_dir

    _validate_project(project_dir)

    logger.info("Initializing djb development environment")

    # Configure all fields using the new orchestrator
    configured = _configure_all_fields(project_dir)
    _sync_identity_to_git()

    user_name = configured.get("name")
    user_email = configured.get("email")
    project_name = configured.get("project_name", config.project_name)

    gitignore_updated = _update_gitignore_for_project_config(project_dir)
    if gitignore_updated:
        logger.done("Added .djb/local.yaml to .gitignore")

    _install_brew_dependencies(skip=skip_brew)
    _install_python_dependencies(project_dir, skip=skip_python)
    _add_djb_to_installed_apps(project_dir)
    _install_frontend_dependencies(project_dir, skip=skip_frontend)
    _init_database(project_dir, skip=skip_db)
    _run_migrations(project_dir, skip=skip_migrations)
    _run_seed(skip=skip_seed)
    _install_git_hooks(project_dir, skip=skip_hooks)
    _init_secrets(project_dir, user_email, user_name, project_name, skip=skip_secrets)
    _auto_commit_project_config(project_dir, gitignore_updated)
    _show_success_message()
