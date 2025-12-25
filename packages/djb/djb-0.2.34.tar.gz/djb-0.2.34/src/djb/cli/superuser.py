"""
djb sync-superuser CLI - Sync Django superuser from encrypted secrets.
"""

from __future__ import annotations

import subprocess

import click

from djb.cli.context import CliContext, pass_context
from djb.core.logging import get_logger
from djb.cli.utils import run_streaming
from djb.secrets import SECRETS_ENVIRONMENTS

logger = get_logger(__name__)


@click.command("sync-superuser")
@click.option(
    "--environment",
    "-e",
    type=click.Choice(SECRETS_ENVIRONMENTS),
    default=None,
    help="Environment to load secrets from (default: auto-detect)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--app",
    default=None,
    help="Heroku app name (runs on Heroku instead of locally)",
)
@pass_context
def sync_superuser(cli_ctx: CliContext, environment: str | None, dry_run: bool, app: str | None):
    """Sync superuser from encrypted secrets.

    Creates or updates the Django superuser based on credentials stored
    in the encrypted secrets file. Requires the Django project to have
    a `sync_superuser` management command.

    \b
    Examples:
      djb sync-superuser                   # Sync locally (auto-detect env)
      djb sync-superuser -e dev            # Sync using dev secrets
      djb sync-superuser --app myapp       # Sync on Heroku
      djb sync-superuser --dry-run         # Preview changes
    """
    config = cli_ctx.config
    project_dir = config.project_dir

    if app:
        # Run on Heroku - use --no-notify and -- separator for proper arg passing
        cmd = [
            "heroku",
            "run",
            "--no-notify",
            "--app",
            app,
            "--",
            "python",
            "manage.py",
            "sync_superuser",
        ]
        if environment:
            cmd.extend(["--environment", environment])
        if dry_run:
            cmd.append("--dry-run")
        returncode, _, _ = run_streaming(cmd, label=f"Syncing superuser on Heroku ({app})")
        if returncode != 0:
            raise click.ClickException("Failed to sync superuser")
    else:
        # Run locally - use subprocess.run for direct execution
        cmd = ["python", "manage.py", "sync_superuser"]
        if environment:
            cmd.extend(["--environment", environment])
        if dry_run:
            cmd.append("--dry-run")
        logger.next("Syncing superuser locally")
        result = subprocess.run(cmd, cwd=project_dir)
        if result.returncode != 0:
            raise click.ClickException("Failed to sync superuser")
