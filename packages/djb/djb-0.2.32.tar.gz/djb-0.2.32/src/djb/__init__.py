"""
djb - Django + Bun deployment platform.

A simplified, self-contained deployment platform for Django applications.

Quick start:
    from djb import config, get_logger, setup_logging

    setup_logging()
    logger = get_logger(__name__)
    logger.info(f"Running in {config.mode} mode")

Public API:
    __version__ - Package version string

    Logging:
        setup_logging - Initialize the djb logging system
        get_logger - Get a logger instance for a module
        Level - Enum of log levels (DEBUG, INFO, etc.)
        DjbLogger - Logger class for CLI output formatting

    Configuration:
        config - Lazy configuration (like Django's settings)
        configure - Set CLI overrides before config loads
        reset_config - Reset config singleton to unloaded state (test utility)

    CLI:
        get_cli_epilog - Get djb epilog text for embedding in host project CLIs

See Also:
    djb/README.md - Full documentation
    djb.secrets - Encrypted secrets management
    djb.core - Exception hierarchy
"""

from __future__ import annotations

from djb._version import __version__

# config must be imported first. CLI modules import it from djb during their load.
from djb.config import config, configure, reset_config
from djb.cli.epilog import get_cli_epilog
from djb.core.logging import DjbLogger, Level, get_logger, setup_logging

__all__ = [
    "__version__",
    # Logging
    "DjbLogger",
    "Level",
    "get_logger",
    "setup_logging",
    # Configuration
    "config",
    "configure",
    "reset_config",
    # CLI
    "get_cli_epilog",
]
