"""Tests for djb.types module."""

from __future__ import annotations

import pytest

from djb.types import Mode, Target


class TestMode:
    """Tests for Mode enum."""

    def test_mode_values(self):
        """Test that Mode has expected values."""
        assert Mode.DEVELOPMENT.value == "development"
        assert Mode.STAGING.value == "staging"
        assert Mode.PRODUCTION.value == "production"

    def test_mode_str(self):
        """Test that Mode.__str__ returns value."""
        assert str(Mode.DEVELOPMENT) == "development"
        assert str(Mode.STAGING) == "staging"
        assert str(Mode.PRODUCTION) == "production"

    def test_mode_secrets_env(self):
        """Test secrets_env property."""
        assert Mode.DEVELOPMENT.secrets_env == "dev"
        assert Mode.STAGING.secrets_env == "staging"
        assert Mode.PRODUCTION.secrets_env == "production"

    def test_mode_parse_valid(self):
        """Test Mode.parse with valid values."""
        assert Mode.parse("development") == Mode.DEVELOPMENT
        assert Mode.parse("staging") == Mode.STAGING
        assert Mode.parse("production") == Mode.PRODUCTION

    def test_mode_parse_case_insensitive(self):
        """Test Mode.parse is case insensitive."""
        assert Mode.parse("DEVELOPMENT") == Mode.DEVELOPMENT
        assert Mode.parse("Development") == Mode.DEVELOPMENT
        assert Mode.parse("STAGING") == Mode.STAGING

    def test_mode_parse_none(self):
        """Test Mode.parse with None."""
        assert Mode.parse(None) is None
        assert Mode.parse(None, default=Mode.DEVELOPMENT) == Mode.DEVELOPMENT

    def test_mode_parse_invalid(self):
        """Test Mode.parse with invalid value."""
        assert Mode.parse("invalid") is None
        assert Mode.parse("invalid", default=Mode.DEVELOPMENT) == Mode.DEVELOPMENT
        assert Mode.parse("") is None


class TestTarget:
    """Tests for Target enum."""

    def test_target_values(self):
        """Test that Target has expected values."""
        assert Target.HEROKU.value == "heroku"

    def test_target_str(self):
        """Test that Target.__str__ returns value."""
        assert str(Target.HEROKU) == "heroku"

    def test_target_parse_valid(self):
        """Test Target.parse with valid values."""
        assert Target.parse("heroku") == Target.HEROKU

    def test_target_parse_case_insensitive(self):
        """Test Target.parse is case insensitive."""
        assert Target.parse("HEROKU") == Target.HEROKU
        assert Target.parse("Heroku") == Target.HEROKU

    def test_target_parse_none(self):
        """Test Target.parse with None."""
        assert Target.parse(None) is None
        assert Target.parse(None, default=Target.HEROKU) == Target.HEROKU

    def test_target_parse_invalid(self):
        """Test Target.parse with invalid value."""
        assert Target.parse("invalid") is None
        assert Target.parse("invalid", default=Target.HEROKU) == Target.HEROKU
        assert Target.parse("") is None


class TestModeIsStrEnum:
    """Test that Mode works as both str and Enum."""

    def test_mode_in_string_operations(self):
        """Test Mode can be used in string operations."""
        mode = Mode.DEVELOPMENT
        assert mode == "development"
        assert f"mode: {mode}" == "mode: development"

    def test_mode_in_dict_keys(self):
        """Test Mode can be used as dict keys and compared to strings."""
        config = {Mode.DEVELOPMENT: "dev config", Mode.PRODUCTION: "prod config"}
        # Can access by Mode
        assert config[Mode.DEVELOPMENT] == "dev config"


class TestTargetIsStrEnum:
    """Test that Target works as both str and Enum."""

    def test_target_in_string_operations(self):
        """Test Target can be used in string operations."""
        target = Target.HEROKU
        assert target == "heroku"
        assert f"target: {target}" == "target: heroku"
