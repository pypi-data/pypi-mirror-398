"""
djb.cli.utils - Utility functions for djb CLI.

Run functions:
    run_cmd - Run a shell command with optional error handling
    check_cmd - Check if a command succeeds
    run_streaming - Run a command while streaming output to terminal

Internal run functions (for testing):
    _get_clean_env - Get environment with VIRTUAL_ENV cleared
    _run_streaming_threads - Threaded implementation for Windows

Other utilities:
    flatten_dict - Flatten a nested dictionary into a flat dict with uppercase keys
"""

from __future__ import annotations

from .flatten import flatten_dict
from .run import (
    _get_clean_env,
    _run_streaming_threads,
    check_cmd,
    run_cmd,
    run_streaming,
)

__all__ = [
    "_get_clean_env",
    "_run_streaming_threads",
    "check_cmd",
    "flatten_dict",
    "run_cmd",
    "run_streaming",
]
