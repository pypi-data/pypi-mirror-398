"""
djb CLI - Main command-line interface.

Provides subcommands for secrets management, deployment, and development.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from djb._version import __version__
from djb.cli.config_cmd import config_group
from djb.cli.context import CliContext
from djb.cli.db import db
from djb.cli.deploy import deploy
from djb.cli.dependencies import dependencies
from djb.cli.editable import editable_djb
from djb.cli.health import health
from djb.cli.init import init
from djb.core.logging import Colors, get_logger, setup_logging
from djb.cli.publish import publish
from djb.cli.secrets import secrets
from djb.cli.seed import seed
from djb.cli.superuser import sync_superuser
from djb.config import DjbConfig, config, configure
from djb.types import Mode, Target

logger = get_logger(__name__)


def print_banner(config: DjbConfig) -> None:
    """Print the djb banner showing current mode and target.

    Colors:
    - development: green
    - staging: cyan/blue
    - production: red
    """
    mode_colors = {
        Mode.DEVELOPMENT: Colors.GREEN,
        Mode.STAGING: Colors.CYAN,
        Mode.PRODUCTION: Colors.RED,
    }

    mode_color = mode_colors.get(config.mode, "")
    mode_str = f"{mode_color}{config.mode}{Colors.RESET}"
    target_str = str(config.target)

    logger.info(f"[djb] mode: {mode_str} | target: {target_str}")


@click.group()
@click.version_option(version=__version__, prog_name="djb")
@click.option(
    "--log-level",
    type=click.Choice(["error", "warning", "info", "note", "debug"], case_sensitive=False),
    default=None,
    envvar="DJB_LOG_LEVEL",
    show_envvar=True,
    help="Set logging verbosity level (default: from config or 'info')",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output (e.g., error messages on failure)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output",
)
@click.option(
    "--frontend",
    "scope_frontend",
    is_flag=True,
    help="Limit scope to frontend tasks only",
)
@click.option(
    "--backend",
    "scope_backend",
    is_flag=True,
    help="Limit scope to backend tasks only",
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    envvar="DJB_PROJECT_DIR",
    show_envvar=True,
    help="Project root directory (default: auto-detect).",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["development", "staging", "production"], case_sensitive=False),
    default=None,
    envvar="DJB_MODE",
    show_envvar=True,
    help="Deployment mode (persists to config when set).",
)
@click.option(
    "--target",
    "-t",
    # Note: Only "heroku" is currently supported. Additional targets (docker, k8s)
    # are defined in djb.types.Target but not yet implemented.
    type=click.Choice(["heroku"], case_sensitive=False),
    default=None,
    envvar="DJB_TARGET",
    show_envvar=True,
    help="Deployment target platform.",
)
@click.pass_context
def djb_cli(
    ctx: click.Context,
    log_level: str | None,
    verbose: bool,
    quiet: bool,
    scope_frontend: bool,
    scope_backend: bool,
    project_dir: Path | None,
    mode: str | None,
    target: str | None,
):
    """djb - Django + Bun deployment platform"""
    # Configure CLI overrides BEFORE accessing the global config
    # This ensures all code importing `from djb import config` sees the overrides
    try:
        configure(
            project_dir=project_dir,
            mode=Mode(mode.lower()) if mode else None,
            target=Target(target.lower()) if target else None,
            log_level=log_level.lower() if log_level else None,
        )
    except ValueError as e:
        raise click.ClickException(str(e))

    # Set up logging using resolved config value (CLI > ENV > local > project > default)
    setup_logging(config.log_level)

    # Persist mode if explicitly set via CLI
    if mode is not None:
        config.save_mode()

    # Validate required config fields (skip for init command which sets them up)
    # Config lazy-loads when first accessed below
    try:
        if ctx.invoked_subcommand != "init":
            missing = []
            if config.project_dir is None:
                missing.append("project_dir")
            if config.project_name is None:
                missing.append("project_name")
            if config.name is None:
                missing.append("name")
            if config.email is None:
                missing.append("email")
            if missing:
                raise click.ClickException(
                    f"Missing required config: {', '.join(missing)}. "
                    f"Run 'djb init' from your project directory to set up configuration."
                )
    except ValueError as e:
        raise click.ClickException(str(e))

    # Store in context for subcommands
    ctx.ensure_object(CliContext)
    if not isinstance(ctx.obj, CliContext):
        raise click.ClickException("Internal error: context object is not CliContext")
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet
    ctx.obj.scope_frontend = scope_frontend
    ctx.obj.scope_backend = scope_backend
    ctx.obj.config = config

    # Print banner (unless nested invocation, quiet mode, or pipe-friendly command)
    # Commands that output data for piping should not print the banner
    pipe_friendly_commands = {"secrets export-key"}
    command_path = " ".join(
        arg for arg in sys.argv[1:] if not arg.startswith("-") and not arg.startswith("--")
    )
    is_pipe_friendly = any(command_path.startswith(cmd) for cmd in pipe_friendly_commands)

    if not os.environ.get("DJB_NESTED") and not quiet and not is_pipe_friendly:
        print_banner(config)


# Add subcommands
djb_cli.add_command(init)
djb_cli.add_command(db)
djb_cli.add_command(secrets)
djb_cli.add_command(deploy)
djb_cli.add_command(dependencies)
djb_cli.add_command(health)
djb_cli.add_command(publish)
djb_cli.add_command(editable_djb)
djb_cli.add_command(sync_superuser)
djb_cli.add_command(config_group)
djb_cli.add_command(seed)


@djb_cli.command("help")
@click.pass_context
def help_cmd(ctx: click.Context) -> None:
    """Show this help message."""
    # Get the parent (djb_cli) context and print its help
    if ctx.parent is not None:
        logger.info(ctx.parent.get_help())


def main():
    """Entry point for djb CLI."""
    djb_cli()


if __name__ == "__main__":
    main()
