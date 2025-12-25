"""Tests for djb.config.prompting module; interactive prompting functions."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from djb.config.prompting import PromptResult, confirm, prompt


class TestPromptResult:
    """Tests for PromptResult dataclass."""

    def test_creation_with_user_source(self):
        """Test PromptResult can be created with user source."""
        result = PromptResult(value="test-value", source="user", attempts=1)

        assert result.value == "test-value"
        assert result.source == "user"
        assert result.attempts == 1

    def test_creation_with_default_source(self):
        """Test PromptResult can be created with default source."""
        result = PromptResult(value="default-value", source="default", attempts=1)

        assert result.value == "default-value"
        assert result.source == "default"
        assert result.attempts == 1

    def test_creation_with_cancelled_source(self):
        """Test PromptResult can be created with cancelled source."""
        result = PromptResult(value=None, source="cancelled", attempts=3)

        assert result.value is None
        assert result.source == "cancelled"
        assert result.attempts == 3


class TestPrompt:
    """Tests for prompt() function."""

    def test_returns_user_input(self):
        """Test prompt returns user input with 'user' source."""
        with patch("builtins.input", return_value="test-value"):
            result = prompt("Enter value")

        assert result.value == "test-value"
        assert result.source == "user"
        assert result.attempts == 1

    def test_returns_default_on_empty_input(self):
        """Test prompt returns default when user enters nothing."""
        with patch("builtins.input", return_value=""):
            result = prompt("Enter value", default="default-value")

        assert result.value == "default-value"
        assert result.source == "default"
        assert result.attempts == 1

    def test_strips_whitespace(self):
        """Test prompt strips whitespace from input."""
        with patch("builtins.input", return_value="  test-value  "):
            result = prompt("Enter value")

        assert result.value == "test-value"

    def test_cancelled_on_keyboard_interrupt(self):
        """Test prompt returns cancelled on KeyboardInterrupt (Ctrl+C)."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = prompt("Enter value")

        assert result.value is None
        assert result.source == "cancelled"
        assert result.attempts == 1

    def test_cancelled_on_eof_error(self):
        """Test prompt returns cancelled on EOFError (Ctrl+D)."""
        with patch("builtins.input", side_effect=EOFError):
            result = prompt("Enter value")

        assert result.value is None
        assert result.source == "cancelled"
        assert result.attempts == 1

    def test_prompt_with_default_formatting(self):
        """Test prompt displays default value in brackets."""
        with patch("builtins.input", return_value="user-value") as mock_input:
            prompt("Enter value", default="default-value")

        # Check the prompt string includes default in brackets
        mock_input.assert_called_once()
        prompt_text = mock_input.call_args[0][0]
        assert "Enter value [default-value]:" in prompt_text

    def test_prompt_without_default_formatting(self):
        """Test prompt without default doesn't show brackets."""
        with patch("builtins.input", return_value="user-value") as mock_input:
            prompt("Enter value")

        mock_input.assert_called_once()
        prompt_text = mock_input.call_args[0][0]
        assert prompt_text == "Enter value: "

    def test_validator_accepts_valid_input(self):
        """Test prompt accepts input that passes validator."""
        validator = lambda x: x.startswith("valid-")

        with patch("builtins.input", return_value="valid-input"):
            result = prompt("Enter value", validator=validator)

        assert result.value == "valid-input"
        assert result.source == "user"

    def test_validator_retries_on_invalid_input(self):
        """Test prompt retries when validator fails."""
        validator = lambda x: x.startswith("valid-")
        inputs = iter(["invalid", "valid-input"])

        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            result = prompt("Enter value", validator=validator, max_retries=3)

        assert result.value == "valid-input"
        assert result.attempts == 2

    def test_validator_exhausts_retries(self):
        """Test prompt returns cancelled when validator fails all retries."""
        validator = lambda x: False  # Always fails

        with patch("builtins.input", return_value="invalid"):
            result = prompt("Enter value", validator=validator, max_retries=3)

        assert result.value is None
        assert result.source == "cancelled"
        assert result.attempts == 3

    def test_normalizer_transforms_input(self):
        """Test prompt applies normalizer to input."""
        normalizer = lambda x: x.lower()

        with patch("builtins.input", return_value="TEST-VALUE"):
            result = prompt("Enter value", normalizer=normalizer)

        assert result.value == "test-value"

    def test_normalizer_none_triggers_retry(self):
        """Test prompt retries when normalizer returns None."""
        # First input gets None from normalizer, second is valid
        normalize_calls = [0]

        def normalizer(x: str) -> str | None:
            normalize_calls[0] += 1
            if normalize_calls[0] == 1:
                return None  # Invalid
            return x.lower()

        inputs = iter(["invalid", "valid"])

        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            result = prompt("Enter value", normalizer=normalizer, max_retries=3)

        assert result.value == "valid"
        assert result.attempts == 2

    def test_normalizer_runs_before_validator(self):
        """Test normalizer is applied before validator."""
        normalizer = lambda x: x.lower()
        validator = lambda x: x == "test"  # Expects lowercase

        with patch("builtins.input", return_value="TEST"):
            result = prompt(
                "Enter value",
                normalizer=normalizer,
                validator=validator,
            )

        assert result.value == "test"

    def test_validation_hint_shown_on_failure(self):
        """Test validation_hint is shown when validation fails."""
        validator = lambda x: x == "valid"
        inputs = iter(["invalid", "valid"])

        with (
            patch("builtins.input", side_effect=lambda _: next(inputs)),
            patch("djb.config.prompting.logger") as mock_logger,
        ):
            prompt(
                "Enter value",
                validator=validator,
                validation_hint="expected: valid",
                max_retries=3,
            )

        # Check that warning was called with hint
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "expected: valid" in warning_call

    def test_empty_input_without_default_retries(self):
        """Test empty input without default triggers retry."""
        inputs = iter(["", "", "finally"])

        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            result = prompt("Enter value", max_retries=3)

        assert result.value == "finally"
        assert result.attempts == 3

    def test_empty_input_without_default_exhausts_retries(self):
        """Test empty input without default exhausts retries."""
        with patch("builtins.input", return_value=""):
            result = prompt("Enter value", max_retries=2)

        assert result.value is None
        assert result.source == "cancelled"
        assert result.attempts == 2


class TestConfirm:
    """Tests for confirm() function."""

    def test_yes_returns_true(self):
        """Test confirm returns True for 'y' input."""
        with patch("builtins.input", return_value="y"):
            result = confirm("Proceed?")

        assert result is True

    def test_yes_full_returns_true(self):
        """Test confirm returns True for 'yes' input."""
        with patch("builtins.input", return_value="yes"):
            result = confirm("Proceed?")

        assert result is True

    def test_yes_case_insensitive(self):
        """Test confirm is case insensitive."""
        with patch("builtins.input", return_value="Y"):
            result = confirm("Proceed?")

        assert result is True

        with patch("builtins.input", return_value="YES"):
            result = confirm("Proceed?")

        assert result is True

    def test_no_returns_false(self):
        """Test confirm returns False for 'n' input."""
        with patch("builtins.input", return_value="n"):
            result = confirm("Proceed?")

        assert result is False

    def test_anything_else_returns_false(self):
        """Test confirm returns False for any non-yes input."""
        with patch("builtins.input", return_value="maybe"):
            result = confirm("Proceed?")

        assert result is False

    def test_empty_returns_default_true(self):
        """Test confirm returns default True on empty input."""
        with patch("builtins.input", return_value=""):
            result = confirm("Proceed?", default=True)

        assert result is True

    def test_empty_returns_default_false(self):
        """Test confirm returns default False on empty input."""
        with patch("builtins.input", return_value=""):
            result = confirm("Proceed?", default=False)

        assert result is False

    def test_shows_yn_suffix_default_true(self):
        """Test confirm shows [Y/n] when default is True."""
        with patch("builtins.input", return_value="y") as mock_input:
            confirm("Proceed?", default=True)

        prompt_text = mock_input.call_args[0][0]
        assert "[Y/n]" in prompt_text

    def test_shows_yn_suffix_default_false(self):
        """Test confirm shows [y/N] when default is False."""
        with patch("builtins.input", return_value="y") as mock_input:
            confirm("Proceed?", default=False)

        prompt_text = mock_input.call_args[0][0]
        assert "[y/N]" in prompt_text

    def test_keyboard_interrupt_returns_default(self):
        """Test confirm returns default on KeyboardInterrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = confirm("Proceed?", default=True)

        assert result is True

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = confirm("Proceed?", default=False)

        assert result is False

    def test_eof_error_returns_default(self):
        """Test confirm returns default on EOFError."""
        with patch("builtins.input", side_effect=EOFError):
            result = confirm("Proceed?", default=True)

        assert result is True

    def test_strips_whitespace(self):
        """Test confirm strips whitespace from input."""
        with patch("builtins.input", return_value="  y  "):
            result = confirm("Proceed?")

        assert result is True
