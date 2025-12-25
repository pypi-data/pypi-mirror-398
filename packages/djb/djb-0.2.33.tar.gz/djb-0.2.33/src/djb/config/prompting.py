"""
Prompting functions for interactive configuration.

This module provides:
- prompt: Get user input with validation and retry
- confirm: Get yes/no confirmation
- PromptResult: Result of a prompt operation
"""

from __future__ import annotations

import readline  # noqa: F401 - enables line editing for input()
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from djb.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PromptResult:
    """Result of a prompt operation.

    Attributes:
        value: The entered value, or None if cancelled/exhausted.
        source: Where the value came from:
            - "user": User entered a value
            - "default": User accepted the default
            - "cancelled": User cancelled (Ctrl+C/Ctrl+D) or exhausted retries
        attempts: Number of prompt attempts made.
    """

    value: str | None
    source: Literal["user", "default", "cancelled"]
    attempts: int


def prompt(
    message: str,
    *,
    default: str | None = None,
    validator: Callable[[str], bool] | None = None,
    normalizer: Callable[[str], str | None] | None = None,
    validation_hint: str | None = None,
    max_retries: int = 3,
) -> PromptResult:
    """Prompt user for input with retry on validation failure.

    Args:
        message: The prompt message to display.
        default: Default value shown in brackets, used if user enters nothing.
        validator: Function that returns True if input is valid.
        normalizer: Function that transforms input (e.g., normalize_project_name).
            Called before validator. If it returns None, validation fails.
        validation_hint: Hint shown when validation fails (e.g., "expected: user@domain.com").
        max_retries: Maximum number of retry attempts.

    Returns:
        PromptResult with the value and source information.
    """
    for attempt in range(1, max_retries + 1):
        # Format prompt with default in brackets
        if default:
            display = f"{message} [{default}]: "
        else:
            display = f"{message}: "

        # Get input
        try:
            entered = input(display).strip()
        except (EOFError, KeyboardInterrupt):
            print()  # newline after ^C/^D
            return PromptResult(value=None, source="cancelled", attempts=attempt)

        # Use default if nothing entered
        if not entered:
            if default:
                return PromptResult(value=default, source="default", attempts=attempt)
            # No input and no default - continue to next attempt
            if attempt < max_retries:
                logger.warning(f"Value is required. Try again ({attempt + 1}/{max_retries}).")
            continue

        # Apply normalizer if provided
        value = entered
        if normalizer:
            normalized = normalizer(value)
            if normalized is None:
                # Normalizer returned None - validation failed
                if attempt < max_retries:
                    hint = f" ({validation_hint})" if validation_hint else ""
                    logger.warning(
                        f"Invalid format{hint}. Try again ({attempt + 1}/{max_retries})."
                    )
                continue
            value = normalized

        # Validate
        if validator and not validator(value):
            if attempt < max_retries:
                hint = f" ({validation_hint})" if validation_hint else ""
                logger.warning(f"Invalid format{hint}. Try again ({attempt + 1}/{max_retries}).")
            continue

        # Success
        return PromptResult(value=value, source="user", attempts=attempt)

    # Exhausted retries
    return PromptResult(value=None, source="cancelled", attempts=max_retries)


def confirm(message: str, *, default: bool = True) -> bool:
    """Prompt user for yes/no confirmation.

    Args:
        message: The confirmation message.
        default: Default value if user just presses Enter.

    Returns:
        True for yes, False for no.
    """
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        response = input(f"{message} {suffix}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()  # newline after ^C/^D
        return default

    if not response:
        return default
    return response in ("y", "yes")
