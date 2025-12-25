"""CLI epilog generation for host projects."""

from __future__ import annotations

import click

from djb.cli.djb import djb_cli


def get_cli_epilog() -> str:
    """Get epilog text for host project CLIs.

    Dynamically generates a formatted string showing djb commands
    by introspecting the actual djb CLI.

    Example:
        from djb.cli.epilog import get_cli_epilog

        @click.group(epilog=get_cli_epilog())
        def my_cli():
            pass
    """
    lines = [
        "\b",
        "For deployment, health checks, and secrets operations, use the djb CLI:",
    ]

    # Create a minimal context just for listing commands
    ctx = click.Context(djb_cli, info_name="djb")
    commands = djb_cli.list_commands(ctx)

    for name in commands:
        cmd = djb_cli.get_command(ctx, name)
        if cmd is None:
            continue
        # Get short help (first line of docstring)
        help_text = cmd.get_short_help_str(limit=50)
        lines.append(f"  djb {name:24} {help_text}")

    lines.append("")
    lines.append("Run 'djb --help' for full documentation.")

    return "\n".join(lines)
