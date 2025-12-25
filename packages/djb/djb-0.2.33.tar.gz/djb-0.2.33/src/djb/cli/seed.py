"""
djb seed CLI - Dynamic seed command loading.

Provides utilities for loading and executing host project seed commands
that are registered via configuration.
"""

from __future__ import annotations

import importlib
import os
from typing import TYPE_CHECKING

import click
import django

from djb import config
from djb.cli.context import CliContext
from djb.core.logging import get_logger

if TYPE_CHECKING:
    from djb.config import DjbConfig

logger = get_logger(__name__)


# Help text shown when no seed_command is configured
_UNCONFIGURED_HELP = """\
Run the host project's seed command.

No seed_command is currently configured. To use this command, register
your project's seed command:

  djb config seed_command myapp.cli.seed:seed

The value should be a module:attribute path to a Click command decorated
with @click.command(). The command will receive any additional arguments
you pass to 'djb seed'.

Example seed command in your project:

  @click.command()
  @click.option("--truncate", is_flag=True)
  def seed(truncate):
      # Your seeding logic here
      pass
"""


class DynamicHelpSeedCommand(click.Command):
    """A Click command that shows dynamic help based on seed_command configuration."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Format help, showing host command help if configured."""
        seed_command_path = config.seed_command
        host_command = load_seed_command(seed_command_path) if seed_command_path else None

        if host_command is None:
            # No seed command configured - show configuration instructions
            formatter.write(_UNCONFIGURED_HELP)
        else:
            # Show djb preamble + host command help
            formatter.write("Run the host project's seed command.\n\n")
            formatter.write(f"Configured seed command: {seed_command_path}\n\n")
            formatter.write("--- Host command help ---\n\n")

            # Get help from host command
            with click.Context(host_command) as host_ctx:
                host_command.format_help(host_ctx, formatter)


@click.command(
    "seed",
    cls=DynamicHelpSeedCommand,
    context_settings={
        "allow_extra_args": True,
        "allow_interspersed_args": False,
        "ignore_unknown_options": True,
    },
)
@click.pass_context
def seed(ctx: click.Context) -> None:
    """Run the host project's seed command."""
    # Get config from Click context - already loaded by djb.py and passed via context
    ctx_obj = ctx.find_object(CliContext)
    if ctx_obj is None:
        raise click.ClickException("Internal error: CliContext not found")
    cfg = ctx_obj.config

    seed_command_path = cfg.seed_command
    if not seed_command_path:
        raise click.ClickException(
            "No seed_command configured.\n\n"
            "Configure a seed command with:\n"
            "  djb config seed_command myapp.cli.seed:seed\n\n"
            "The value should be a module:attribute path to a Click command."
        )

    # Initialize Django before loading the host command
    # Uses project_name from config to derive settings module (e.g., "myapp.settings")
    # This is idempotent - if the host command also calls django.setup(), it's a no-op
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{cfg.project_name}.settings")
    django.setup()

    host_command = load_seed_command(seed_command_path)
    if host_command is None:
        raise click.ClickException(
            f"Could not load seed_command: {seed_command_path}\n\n"
            "Check that the module and attribute exist and are accessible."
        )

    # Invoke the host command with any extra args
    # Create a new context for the host command
    with host_command.make_context("seed", ctx.args, parent=ctx) as host_ctx:
        host_command.invoke(host_ctx)


def load_seed_command(seed_command: str) -> click.Command | None:
    """Load a Click command from a module:attr string.

    Args:
        seed_command: Module path and attribute name (e.g., "beachresort25.cli.seed:seed")

    Returns:
        The Click command, or None if loading failed.
    """
    try:
        module_path, attr_name = seed_command.split(":")
        module = importlib.import_module(module_path)
        command = getattr(module, attr_name)
        if not isinstance(command, click.Command):
            logger.warning(f"seed_command '{seed_command}' is not a Click command")
            return None
        return command
    except ValueError:
        logger.warning(
            f"Invalid seed_command format: '{seed_command}'. " "Expected 'module.path:attribute'"
        )
        return None
    except ImportError as e:
        logger.warning(f"Could not import seed_command module '{seed_command}': {e}")
        return None
    except AttributeError as e:
        logger.warning(f"Could not find seed_command attribute '{seed_command}': {e}")
        return None


def run_seed_command(config: DjbConfig) -> bool:
    """Run the seed command programmatically.

    Args:
        config: The djb configuration containing the seed_command setting.

    Returns:
        True if successful, False otherwise.
    """
    if not config.seed_command:
        logger.warning("No seed_command configured")
        return False

    command = load_seed_command(config.seed_command)
    if command is None:
        return False

    try:
        # Create a Click context and invoke the command
        # standalone_mode=False prevents sys.exit on completion
        ctx = click.Context(command)
        with ctx:
            command.invoke(ctx)
        return True
    except click.ClickException as e:
        logger.error(f"Seed failed: {e.message}")
        return False
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        return False
