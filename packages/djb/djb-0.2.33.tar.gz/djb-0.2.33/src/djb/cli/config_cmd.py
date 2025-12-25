"""
djb config CLI - Manage djb configuration.

Provides a discoverable, documented interface for viewing and modifying
djb settings. Each config option is a subcommand with its own documentation.
"""

from __future__ import annotations

import json
from typing import Any, cast

import attrs
import click

from djb.cli.context import CliContext, pass_context
from djb.core.logging import get_logger
from djb.config import (
    ATTRSLIB_METADATA_KEY,
    PROJECT,
    ConfigFileType,
    ConfigValidationError,
    DjbConfig,
    load_config,
    save_config,
)
from djb.config.field import ConfigFieldABC

logger = get_logger(__name__)


def _format_json_with_provenance(config: DjbConfig) -> str:
    """Format config as JSON with aligned provenance comments.

    Produces output like:
        {
          "project_dir": "/path/to/project",  // project_config
          "mode": "development",              // local_config
          "name": null                        // (not set)
        }
    """
    config_dict = config.to_dict()

    # Build lines with values and provenance
    lines: list[tuple[str, str, str]] = []  # (key, json_value, provenance)
    for key, value in config_dict.items():
        json_value = json.dumps(value)
        source = config.get_source(key)
        if source is not None:
            provenance = source.value
        else:
            provenance = "(not set)"
        lines.append((key, json_value, provenance))

    # Calculate alignment: find max length of "key": value portion
    key_value_parts = [f'  "{key}": {json_value}' for key, json_value, _ in lines]
    max_len = max(len(part) for part in key_value_parts)

    # Build output with aligned comments
    output_lines = ["{"]
    for i, ((key, json_value, provenance), kv_part) in enumerate(zip(lines, key_value_parts)):
        # Add comma for all but last line (extra space when no comma to keep alignment)
        comma = "," if i < len(lines) - 1 else " "
        # Pad to align comments
        padding = " " * (max_len - len(kv_part))
        output_lines.append(f"{kv_part}{comma}{padding}  // {provenance}")
    output_lines.append("}")

    return "\n".join(output_lines)


def _get_field_metadata(field_name: str) -> ConfigFieldABC:
    """Get the ConfigField metadata for a DjbConfig field."""
    for field in attrs.fields(DjbConfig):
        if field.name == field_name:
            config_field = field.metadata.get(ATTRSLIB_METADATA_KEY)
            if config_field is None:
                raise ValueError(f"{field_name} is not a config field")
            config_field.field_name = field_name
            return config_field
    raise ValueError(f"Unknown field: {field_name}")


def _config_get_set_delete(
    cli_ctx: CliContext,
    field_name: str,
    value: Any | None,
    delete: bool,
) -> None:
    """Handle get/set/delete for a config field using DjbConfig metadata.

    Args:
        cli_ctx: CLI context with loaded config.
        field_name: Name of the DjbConfig field.
        value: New value to set, or None to show current.
        delete: If True, remove the field from config.
    """
    config = cli_ctx.config
    project_root = config.project_dir
    current_value = getattr(config, field_name)

    # Get field metadata for config file info
    field_meta = _get_field_metadata(field_name)
    config_file = cast(ConfigFileType, field_meta.config_file or PROJECT)
    file_key = field_meta.config_file_key or field_name

    if delete:
        # Only delete if the value comes from a config file we can modify
        source = config.get_source(field_name)
        config_file_type = source.config_file_type if source else None
        if config_file_type is not None:
            file_config = load_config(config_file_type, project_root)
            file_config.pop(file_key, None)
            save_config(config_file_type, file_config, project_root)
            logger.done(f"{field_name} removed")
        elif current_value is not None:
            # Value exists but comes from env, CLI, pyproject, git, etc.
            source_name = source.value if source else "unknown"
            logger.warning(f"{field_name} is set from {source_name}, not from a config file")
        else:
            logger.info(f"{field_name}: (not set)")
    elif value is None:
        # Show current value
        if current_value is not None:
            logger.info(f"{field_name}: {current_value}")
        else:
            logger.info(f"{field_name}: (not set)")
    else:
        # Validate using the field's validate() method
        try:
            field_meta.validate(value)
        except ConfigValidationError as e:
            raise click.ClickException(str(e))

        # Set new value in config file
        file_config = load_config(config_file, project_root)
        file_config[file_key] = value
        save_config(config_file, file_config, project_root)
        logger.done(f"{field_name} set to: {value}")


@click.group("config", invoke_without_command=True)
@click.option(
    "--show",
    "show_config",
    is_flag=True,
    help="Print the merged configuration as JSON.",
)
@click.option(
    "--with-provenance",
    "with_provenance",
    is_flag=True,
    help="Include provenance comments showing where each value came from.",
)
@click.pass_context
def config_group(ctx: click.Context, show_config: bool, with_provenance: bool) -> None:
    """Manage djb configuration.

    View and modify djb settings. Each subcommand manages a specific
    configuration option with its own documentation.

    Environment variables (DJB_*) are documented in each subcommand's help.

    \b
    Examples:
      djb config --show                           # Show all config as JSON
      djb config --show --with-provenance         # Show config with sources
      djb config seed_command                     # Show current value
      djb config seed_command myapp.cli:seed      # Set seed command
    """
    if show_config or with_provenance:
        if with_provenance:
            logger.info(_format_json_with_provenance(ctx.obj.config))
        else:
            logger.info(ctx.obj.config.to_json())
        ctx.exit(0)
    elif ctx.invoked_subcommand is None:
        # No subcommand and no --list, show help
        logger.info(ctx.get_help())


@config_group.command("seed_command")
@click.argument("value", required=False)
@click.option(
    "--delete",
    is_flag=True,
    help="Remove the seed_command setting.",
)
@pass_context
def config_seed_command(cli_ctx: CliContext, value: str | None, delete: bool) -> None:
    """Configure the host project's seed command.

    The seed command is a Click command from your project that djb will:

    \b
    * Register as 'djb seed' for manual execution
    * Run automatically during 'djb init' after migrations

    The value should be a module:attribute path to a Click command.
    Stored in .djb/project.yaml (shared, committed).

    Can also be set via the DJB_SEED_COMMAND environment variable.

    \b
    Examples:
      djb config seed_command                           # Show current
      djb config seed_command myapp.cli.seed:seed       # Set command
      djb config seed_command --delete                  # Remove setting

    \b
    Your seed command should:
      * Be a Click command (decorated with @click.command())
      * Handle Django setup internally (call django.setup())
      * Be idempotent (safe to run multiple times)
    """
    _config_get_set_delete(cli_ctx, "seed_command", value, delete)


@config_group.command("project_name")
@click.argument("value", required=False)
@click.option(
    "--delete",
    is_flag=True,
    help="Remove the project_name setting.",
)
@pass_context
def config_project_name(cli_ctx: CliContext, value: str | None, delete: bool) -> None:
    """Configure the project name.

    The project name is used for deployment identifiers, Heroku app names,
    and Kubernetes labels. Must be a valid DNS label (lowercase alphanumeric
    with hyphens, max 63 chars, starts/ends with alphanumeric).

    If not set explicitly, defaults to the project name from pyproject.toml.

    Can also be set via the DJB_PROJECT_NAME environment variable.

    \b
    Examples:
      djb config project_name                  # Show current
      djb config project_name my-app           # Set name
      djb config project_name --delete         # Remove (use pyproject.toml)
    """
    _config_get_set_delete(cli_ctx, "project_name", value, delete)


@config_group.command("name")
@click.argument("value", required=False)
@click.option(
    "--delete",
    is_flag=True,
    help="Remove the name setting.",
)
@pass_context
def config_name(cli_ctx: CliContext, value: str | None, delete: bool) -> None:
    """Configure the user name.

    The name is used for git commits and secrets management (GPG key
    generation). Stored in .djb/local.yaml (gitignored, per-user).

    Can also be set via the DJB_NAME environment variable.

    \b
    Examples:
      djb config name                          # Show current
      djb config name "Jane Doe"               # Set name
      djb config name --delete                 # Remove setting
    """
    _config_get_set_delete(cli_ctx, "name", value, delete)


@config_group.command("email")
@click.argument("value", required=False)
@click.option(
    "--delete",
    is_flag=True,
    help="Remove the email setting.",
)
@pass_context
def config_email(cli_ctx: CliContext, value: str | None, delete: bool) -> None:
    """Configure the user email.

    The email is used for git commits and secrets management (GPG key
    generation). Stored in .djb/local.yaml (gitignored, per-user).

    Can also be set via the DJB_EMAIL environment variable.

    \b
    Examples:
      djb config email                         # Show current
      djb config email jane@example.com        # Set email
      djb config email --delete                # Remove setting
    """
    _config_get_set_delete(cli_ctx, "email", value, delete)


@config_group.command("hostname")
@click.argument("value", required=False)
@click.option(
    "--delete",
    is_flag=True,
    help="Remove the hostname setting.",
)
@pass_context
def config_hostname(cli_ctx: CliContext, value: str | None, delete: bool) -> None:
    """Configure the production hostname.

    The hostname is used for ALLOWED_HOSTS in production deployments.
    Stored in .djb/project.yaml (shared, committed).

    Can also be set via the DJB_HOSTNAME environment variable.

    \b
    Examples:
      djb config hostname                      # Show current
      djb config hostname example.com          # Set hostname
      djb config hostname --delete             # Remove setting
    """
    _config_get_set_delete(cli_ctx, "hostname", value, delete)
