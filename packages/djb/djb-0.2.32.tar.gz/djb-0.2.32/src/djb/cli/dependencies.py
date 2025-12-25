"""Dependency management command."""

from __future__ import annotations

import click

from djb.cli.context import CliContext, pass_context
from djb.core.logging import get_logger
from djb.cli.utils import run_streaming

logger = get_logger(__name__)


@click.command(name="dependencies")
@click.option(
    "--bump",
    is_flag=True,
    help="Upgrade to the latest available versions (uv lock --upgrade --latest for backend, bun update --latest for frontend).",
)
@pass_context
def dependencies(cli_ctx: CliContext, bump: bool) -> None:
    """Refresh dependencies for frontend and/or backend.

    Updates lock files and installs dependencies:

    \b
    Backend (--backend):
      * Runs uv lock --upgrade to update lockfile
      * Runs uv sync to install dependencies
      * With --bump: uses --latest to get newest versions

    \b
    Frontend (--frontend):
      * Runs bun install to sync dependencies
      * With --bump: runs bun update --latest

    \b
    Examples:
      djb --backend dependencies                 # Refresh backend only
      djb --frontend dependencies                # Refresh frontend only
      djb --backend --frontend dependencies      # Refresh both
      djb --backend dependencies --bump          # Upgrade to latest versions
    """
    scope_frontend = cli_ctx.scope_frontend
    scope_backend = cli_ctx.scope_backend

    if not scope_frontend and not scope_backend:
        raise click.ClickException(
            "Specify --frontend and/or --backend to choose which deps to refresh."
        )

    config = cli_ctx.config
    project_dir = config.project_dir

    if scope_backend:
        bump_str = "yes" if bump else "no"
        logger.info(f"Refreshing Python deps with uv (bump={bump_str})...")
        lock_cmd = ["uv", "lock", "--upgrade"]
        if bump:
            lock_cmd.append("--latest")
        returncode, _, _ = run_streaming(lock_cmd, cwd=project_dir, label="uv lock")
        if returncode != 0:
            raise click.ClickException("uv lock failed")

        returncode, _, _ = run_streaming(["uv", "sync"], cwd=project_dir, label="uv sync")
        if returncode != 0:
            raise click.ClickException("uv sync failed")

        logger.done("Backend dependencies refreshed.")

    if scope_frontend:
        bump_str = "yes" if bump else "no"
        logger.info(f"Refreshing frontend deps with Bun (bump={bump_str})...")
        frontend_dir = project_dir / "frontend"
        # Reuse the existing Bun helper script to keep logic in one place
        cmd = ["bun", "run", "refresh-deps"]
        if bump:
            cmd.append("--bump")
        returncode, _, _ = run_streaming(cmd, cwd=frontend_dir, label="frontend refresh-deps")
        if returncode != 0:
            raise click.ClickException("frontend refresh-deps failed")

        logger.done("Frontend dependencies refreshed.")
