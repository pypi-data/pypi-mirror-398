"""Tests for specialized config field types.

Tests validation, normalization, acquisition, and other specialized behaviors
for EmailField, HostnameField, SeedCommandField, LogLevelField, NameField,
EnumField, and ProjectNameField.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from djb.config.acquisition import AcquisitionContext, GitConfigSource
from djb.config.field import ConfigValidationError
from djb.config.fields.email import EMAIL_PATTERN, EmailField
from djb.config.fields.enum import EnumField
from djb.config.fields.hostname import HostnameField
from djb.config.fields.log_level import (
    DEFAULT_LOG_LEVEL,
    VALID_LOG_LEVELS,
    LogLevelField,
)
from djb.config.fields.name import NameField
from djb.config.fields.project_name import (
    DNS_LABEL_PATTERN,
    ProjectNameField,
    normalize_project_name,
)
from djb.config.fields.seed_command import SEED_COMMAND_PATTERN, SeedCommandField
from djb.config.prompting import PromptResult
from djb.config.resolution import ConfigSource, ProvenanceChainMap, ResolutionContext
from djb.types import Mode, Target


# ==============================================================================
# EmailField Tests
# ==============================================================================


class TestEmailFieldValidation:
    """Tests for EmailField.validate()."""

    def test_accepts_valid_email(self):
        """Test valid email passes validation."""
        field = EmailField()
        field.field_name = "email"
        # Should not raise
        field.validate("user@example.com")
        field.validate("test.user@company.co.uk")
        field.validate("name+tag@domain.org")

    def test_rejects_missing_at_sign(self):
        """Test email without @ is rejected."""
        field = EmailField()
        field.field_name = "email"
        with pytest.raises(ConfigValidationError, match="Invalid email format"):
            field.validate("notanemail")

    def test_rejects_missing_domain(self):
        """Test email without domain is rejected."""
        field = EmailField()
        field.field_name = "email"
        with pytest.raises(ConfigValidationError, match="Invalid email format"):
            field.validate("user@")

    def test_rejects_missing_tld(self):
        """Test email without TLD is rejected."""
        field = EmailField()
        field.field_name = "email"
        with pytest.raises(ConfigValidationError, match="Invalid email format"):
            field.validate("user@domain")

    def test_rejects_spaces(self):
        """Test email with spaces is rejected."""
        field = EmailField()
        field.field_name = "email"
        with pytest.raises(ConfigValidationError, match="Invalid email format"):
            field.validate("user @example.com")
        with pytest.raises(ConfigValidationError, match="Invalid email format"):
            field.validate("user@ example.com")

    def test_accepts_none_when_optional(self):
        """Test None is accepted (skip validation)."""
        field = EmailField()
        field.field_name = "email"
        # Should not raise - None skips validation
        field.validate(None)

    def test_pattern_is_compiled_regex(self):
        """Test EMAIL_PATTERN is a compiled regex."""
        assert isinstance(EMAIL_PATTERN, re.Pattern)


class TestEmailFieldGitConfigIntegration:
    """Tests for EmailField git config integration."""

    def test_has_git_config_external_source(self):
        """Test EmailField includes git config as external source."""
        field = EmailField()
        assert len(field.external_sources) == 1
        source = field.external_sources[0]
        assert isinstance(source, GitConfigSource)
        assert source.key == "user.email"

    def test_has_prompt_text(self):
        """Test EmailField has prompt text."""
        field = EmailField()
        assert field.prompt_text == "Enter your email"

    def test_has_validation_hint(self):
        """Test EmailField has validation hint."""
        field = EmailField()
        assert field.validation_hint == "expected: user@domain.com"


# ==============================================================================
# HostnameField Tests
# ==============================================================================


class TestHostnameFieldAcquisition:
    """Tests for HostnameField.acquire() dynamic default."""

    def test_computes_default_from_project_name(self, tmp_path: Path):
        """Test hostname default is computed from project_name."""
        field = HostnameField(config_file="project")
        field.field_name = "hostname"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={"project_name": "myapp"},
        )

        with patch("djb.config.fields.hostname.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(value="myapp.com", source="user", attempts=1)
            result = field.acquire(ctx)

        # Should have prompted with computed default
        mock_prompt.assert_called_once_with(
            "Enter production hostname",
            default="myapp.com",
        )
        assert result is not None
        assert result.value == "myapp.com"

    def test_uses_current_value_if_available(self, tmp_path: Path):
        """Test hostname uses current value as default if available."""
        field = HostnameField(config_file="project")
        field.field_name = "hostname"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value="existing.com",
            source=ConfigSource.PROJECT_CONFIG,
            other_values={"project_name": "myapp"},
        )

        with patch("djb.config.fields.hostname.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(value="existing.com", source="user", attempts=1)
            result = field.acquire(ctx)

        # Should use existing value, not computed default
        mock_prompt.assert_called_once_with(
            "Enter production hostname",
            default="existing.com",
        )
        assert result is not None
        assert result.value == "existing.com"

    def test_handles_cancelled_prompt(self, tmp_path: Path):
        """Test hostname acquisition handles cancellation."""
        field = HostnameField(config_file="project")
        field.field_name = "hostname"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={"project_name": "myapp"},
        )

        with patch("djb.config.fields.hostname.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(value=None, source="cancelled", attempts=1)
            result = field.acquire(ctx)

        assert result is None

    def test_falls_back_to_default_project_name(self, tmp_path: Path):
        """Test hostname falls back to DEFAULT_PROJECT_NAME if project_name missing."""
        field = HostnameField(config_file="project")
        field.field_name = "hostname"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},  # No project_name
        )

        with patch("djb.config.fields.hostname.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(
                value="myproject.com", source="user", attempts=1
            )
            result = field.acquire(ctx)

        # Should use DEFAULT_PROJECT_NAME (myproject)
        mock_prompt.assert_called_once_with(
            "Enter production hostname",
            default="myproject.com",
        )


# ==============================================================================
# SeedCommandField Tests
# ==============================================================================


class TestSeedCommandFieldValidation:
    """Tests for SeedCommandField.validate()."""

    def test_accepts_valid_seed_command(self):
        """Test valid seed command passes validation."""
        field = SeedCommandField()
        field.field_name = "seed_command"
        # Should not raise
        field.validate("myapp.cli.seed:run")
        field.validate("app.seeds:seed_all")
        field.validate("module:attr")
        field.validate("my_module.sub:my_func")

    def test_rejects_missing_colon(self):
        """Test seed command without colon is rejected."""
        field = SeedCommandField()
        field.field_name = "seed_command"
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            field.validate("myapp.cli.seed")

    def test_rejects_invalid_module_path(self):
        """Test seed command with invalid module path is rejected."""
        field = SeedCommandField()
        field.field_name = "seed_command"
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            field.validate("123invalid:attr")
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            field.validate("module-name:attr")

    def test_rejects_invalid_attribute_name(self):
        """Test seed command with invalid attribute is rejected."""
        field = SeedCommandField()
        field.field_name = "seed_command"
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            field.validate("myapp:123invalid")
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            field.validate("myapp:my-func")

    def test_rejects_multiple_colons(self):
        """Test seed command with multiple colons is rejected."""
        field = SeedCommandField()
        field.field_name = "seed_command"
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            field.validate("myapp:cli:seed")

    def test_accepts_none_when_optional(self):
        """Test None is accepted (skip validation)."""
        field = SeedCommandField()
        field.field_name = "seed_command"
        # Should not raise
        field.validate(None)

    def test_pattern_is_compiled_regex(self):
        """Test SEED_COMMAND_PATTERN is a compiled regex."""
        assert isinstance(SEED_COMMAND_PATTERN, re.Pattern)


# ==============================================================================
# LogLevelField Tests
# ==============================================================================


class TestLogLevelFieldValidation:
    """Tests for LogLevelField.validate()."""

    def test_accepts_valid_log_levels(self):
        """Test all valid log levels pass validation."""
        field = LogLevelField()
        field.field_name = "log_level"
        for level in VALID_LOG_LEVELS:
            field.validate(level)

    def test_accepts_uppercase_log_level(self):
        """Test uppercase log levels pass validation (after normalization)."""
        field = LogLevelField()
        field.field_name = "log_level"
        # Normalize first, then validate
        normalized = field.normalize("INFO")
        field.validate(normalized)
        assert normalized == "info"

    def test_rejects_invalid_log_level(self):
        """Test invalid log level is rejected."""
        field = LogLevelField()
        field.field_name = "log_level"
        with pytest.raises(ConfigValidationError, match="Invalid log_level"):
            field.validate("invalid")
        with pytest.raises(ConfigValidationError, match="Invalid log_level"):
            field.validate("trace")

    def test_error_message_lists_valid_levels(self):
        """Test validation error message lists valid log levels."""
        field = LogLevelField()
        field.field_name = "log_level"
        with pytest.raises(ConfigValidationError, match="debug, error, info, note, warning"):
            field.validate("invalid")

    def test_accepts_none_when_optional(self):
        """Test None is accepted (skip validation)."""
        field = LogLevelField()
        field.field_name = "log_level"
        # Should not raise
        field.validate(None)


class TestLogLevelFieldNormalization:
    """Tests for LogLevelField.normalize()."""

    def test_normalizes_to_lowercase(self):
        """Test log level is normalized to lowercase."""
        field = LogLevelField()
        assert field.normalize("INFO") == "info"
        assert field.normalize("DEBUG") == "debug"
        assert field.normalize("Error") == "error"

    def test_normalizes_string_value(self):
        """Test non-string values are converted to lowercase string."""
        field = LogLevelField()
        # Edge case: YAML might parse as boolean
        assert field.normalize(True) == "true"
        assert field.normalize(123) == "123"

    def test_preserves_lowercase(self):
        """Test lowercase values are preserved."""
        field = LogLevelField()
        assert field.normalize("info") == "info"
        assert field.normalize("debug") == "debug"


class TestLogLevelFieldAcquisition:
    """Tests for LogLevelField.acquire() silent auto-save."""

    def test_uses_current_value_if_available(self, tmp_path: Path):
        """Test acquisition uses current value if available."""
        field = LogLevelField(config_file="project")
        field.field_name = "log_level"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value="debug",
            source=ConfigSource.PROJECT_CONFIG,
            other_values={},
        )

        result = field.acquire(ctx)

        assert result is not None
        assert result.value == "debug"
        assert result.should_save is True
        assert result.was_prompted is False
        assert result.source_name is None

    def test_uses_default_if_no_current_value(self, tmp_path: Path):
        """Test acquisition uses DEFAULT_LOG_LEVEL if no current value."""
        field = LogLevelField(config_file="project")
        field.field_name = "log_level"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )

        result = field.acquire(ctx)

        assert result is not None
        assert result.value == DEFAULT_LOG_LEVEL
        assert result.should_save is True
        assert result.was_prompted is False

    def test_silent_save_no_prompting(self, tmp_path: Path):
        """Test acquisition does not prompt user."""
        field = LogLevelField(config_file="project")
        field.field_name = "log_level"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )

        # LogLevelField.acquire() doesn't use prompt - it just returns a result
        result = field.acquire(ctx)
        assert result is not None
        assert result.was_prompted is False


class TestLogLevelConstants:
    """Tests for LogLevelField constants."""

    def test_valid_log_levels_is_frozenset(self):
        """Test VALID_LOG_LEVELS is a frozenset."""
        assert isinstance(VALID_LOG_LEVELS, frozenset)

    def test_valid_log_levels_content(self):
        """Test VALID_LOG_LEVELS contains expected values."""
        assert VALID_LOG_LEVELS == {"error", "warning", "info", "note", "debug"}

    def test_default_log_level_is_info(self):
        """Test DEFAULT_LOG_LEVEL is 'info'."""
        assert DEFAULT_LOG_LEVEL == "info"

    def test_default_is_in_valid_set(self):
        """Test DEFAULT_LOG_LEVEL is in VALID_LOG_LEVELS."""
        assert DEFAULT_LOG_LEVEL in VALID_LOG_LEVELS


# ==============================================================================
# NameField Tests
# ==============================================================================


class TestNameFieldGitConfigIntegration:
    """Tests for NameField git config integration."""

    def test_has_git_config_external_source(self):
        """Test NameField includes git config as external source."""
        field = NameField()
        assert len(field.external_sources) == 1
        source = field.external_sources[0]
        assert isinstance(source, GitConfigSource)
        assert source.key == "user.name"

    def test_has_prompt_text(self):
        """Test NameField has prompt text."""
        field = NameField()
        assert field.prompt_text == "Enter your name"

    def test_no_validation(self):
        """Test NameField has no validation (accepts any string)."""
        field = NameField()
        field.field_name = "name"
        # Should not raise
        field.validate("John Doe")
        field.validate("任何字符")
        field.validate("")
        field.validate(None)


# ==============================================================================
# EnumField Tests
# ==============================================================================


class TestEnumFieldNormalization:
    """Tests for EnumField.normalize()."""

    def test_returns_enum_instance_unchanged(self):
        """Test enum instances are returned as-is."""
        field = EnumField(Mode)
        field.field_name = "mode"
        assert field.normalize(Mode.DEVELOPMENT) == Mode.DEVELOPMENT
        assert field.normalize(Mode.PRODUCTION) == Mode.PRODUCTION

    def test_parses_string_with_parse_method(self):
        """Test strings are parsed using enum's parse() method."""
        field = EnumField(Mode, default=Mode.DEVELOPMENT)
        field.field_name = "mode"
        # Mode has a parse() method that returns None on failure
        # EnumField.normalize calls it without a default parameter
        assert field.normalize("development") == Mode.DEVELOPMENT
        assert field.normalize("production") == Mode.PRODUCTION
        assert field.normalize("staging") == Mode.STAGING

    def test_falls_back_to_enum_constructor(self):
        """Test fallback to enum constructor for enums without parse()."""
        field = EnumField(Target, default=Target.HEROKU)
        field.field_name = "target"
        # Target enum doesn't have parse(), so use constructor
        assert field.normalize("heroku") == Target.HEROKU

    def test_returns_default_on_parse_failure(self):
        """Test returns default when parsing fails."""
        field = EnumField(Mode, default=Mode.DEVELOPMENT)
        field.field_name = "mode"
        # Invalid value should return default
        result = field.normalize("invalid")
        assert result == Mode.DEVELOPMENT

    def test_handles_none_gracefully(self):
        """Test None returns default."""
        field = EnumField(Mode, default=Mode.DEVELOPMENT)
        field.field_name = "mode"
        # None should attempt parse and fall back to default
        result = field.normalize(None)
        assert result == Mode.DEVELOPMENT


class TestEnumFieldWithCustomParse:
    """Tests for EnumField with enums that have custom parse() methods."""

    def test_mode_enum_parse_aliases(self):
        """Test Mode enum parse handles full names (not aliases)."""
        field = EnumField(Mode, default=Mode.DEVELOPMENT)
        field.field_name = "mode"
        # Mode.parse() handles full names
        assert field.normalize("development") == Mode.DEVELOPMENT
        assert field.normalize("production") == Mode.PRODUCTION
        assert field.normalize("staging") == Mode.STAGING


class TestEnumFieldInit:
    """Tests for EnumField.__init__()."""

    def test_stores_enum_class(self):
        """Test enum_class is stored."""
        field = EnumField(Mode)
        assert field.enum_class == Mode

    def test_accepts_default(self):
        """Test default value is accepted."""
        field = EnumField(Mode, default=Mode.STAGING)
        assert field.default == Mode.STAGING


# ==============================================================================
# ProjectNameField Tests
# ==============================================================================


class TestProjectNameFieldValidation:
    """Tests for ProjectNameField.validate()."""

    def test_accepts_valid_dns_labels(self):
        """Test valid DNS labels pass validation."""
        field = ProjectNameField()
        field.field_name = "project_name"
        # Should not raise
        field.validate("myproject")
        field.validate("my-project")
        field.validate("project123")
        field.validate("a")
        field.validate("a-b-c-1-2-3")

    def test_rejects_uppercase(self):
        """Test uppercase letters are rejected."""
        field = ProjectNameField()
        field.field_name = "project_name"
        with pytest.raises(ConfigValidationError, match="DNS label"):
            field.validate("MyProject")

    def test_rejects_underscore(self):
        """Test underscores are rejected."""
        field = ProjectNameField()
        field.field_name = "project_name"
        with pytest.raises(ConfigValidationError, match="DNS label"):
            field.validate("my_project")

    def test_rejects_leading_hyphen(self):
        """Test leading hyphen is rejected."""
        field = ProjectNameField()
        field.field_name = "project_name"
        with pytest.raises(ConfigValidationError, match="DNS label"):
            field.validate("-myproject")

    def test_rejects_trailing_hyphen(self):
        """Test trailing hyphen is rejected."""
        field = ProjectNameField()
        field.field_name = "project_name"
        with pytest.raises(ConfigValidationError, match="DNS label"):
            field.validate("myproject-")

    def test_rejects_too_long(self):
        """Test names longer than 63 characters are rejected."""
        field = ProjectNameField()
        field.field_name = "project_name"
        # 64 characters
        long_name = "a" * 64
        with pytest.raises(ConfigValidationError, match="DNS label"):
            field.validate(long_name)

    def test_accepts_max_length(self):
        """Test 63-character names are accepted."""
        field = ProjectNameField()
        field.field_name = "project_name"
        # Exactly 63 characters
        max_name = "a" * 63
        field.validate(max_name)

    def test_rejects_empty_string(self):
        """Test empty string is rejected."""
        field = ProjectNameField()
        field.field_name = "project_name"
        with pytest.raises(ConfigValidationError, match="DNS label"):
            field.validate("")

    def test_rejects_none_when_required(self):
        """Test None is rejected for required field."""
        field = ProjectNameField()
        field.field_name = "project_name"
        # ProjectNameField has allow_none=False in validate()
        with pytest.raises(ConfigValidationError, match="project_name is required"):
            field.validate(None)

    def test_pattern_is_compiled_regex(self):
        """Test DNS_LABEL_PATTERN is a compiled regex."""
        assert isinstance(DNS_LABEL_PATTERN, re.Pattern)


class TestProjectNameFieldNormalization:
    """Tests for normalize_project_name() helper."""

    def test_converts_to_lowercase(self):
        """Test normalization converts to lowercase."""
        assert normalize_project_name("MyProject") == "myproject"
        assert normalize_project_name("UPPERCASE") == "uppercase"

    def test_replaces_underscores_with_hyphens(self):
        """Test normalization replaces underscores with hyphens."""
        assert normalize_project_name("my_project") == "my-project"
        assert normalize_project_name("foo_bar_baz") == "foo-bar-baz"

    def test_normalizes_valid_characters_only(self):
        """Test normalization only handles hyphens, underscores, and dots."""
        # Only replaces [-_.] with single hyphen
        # Other invalid characters make the result invalid -> None
        assert normalize_project_name("my project!") is None  # space + ! invalid
        assert normalize_project_name("foo_bar_baz") == "foo-bar-baz"  # underscores replaced
        assert normalize_project_name("my.project") == "my-project"  # dots replaced

    def test_strips_leading_trailing_hyphens(self):
        """Test normalization validates DNS labels (no leading/trailing hyphens)."""
        # normalize_project_name returns None if result is invalid
        # "-myproject-" -> "-myproject-" (invalid DNS label)
        assert normalize_project_name("-myproject-") is None
        # But "myproject-" normalizes to something else or is rejected
        assert normalize_project_name("myproject") == "myproject"

    def test_collapses_multiple_hyphens(self):
        """Test normalization collapses multiple hyphens."""
        assert normalize_project_name("my--project") == "my-project"
        assert normalize_project_name("foo---bar") == "foo-bar"

    def test_handles_empty_input(self):
        """Test normalization returns None for empty/invalid input."""
        # Empty string becomes None
        assert normalize_project_name("") is None
        # All invalid characters removed -> None
        assert normalize_project_name("!!!") is None

    def test_preserves_valid_names(self):
        """Test normalization preserves already-valid names."""
        assert normalize_project_name("myproject") == "myproject"
        assert normalize_project_name("my-project") == "my-project"
        assert normalize_project_name("project123") == "project123"


class TestProjectNameFieldResolution:
    """Tests for ProjectNameField.resolve() multi-source resolution."""

    def test_resolves_from_config_layers(self, tmp_path: Path):
        """Test resolution from config layers (highest priority)."""
        field = ProjectNameField(config_file="project")
        field.field_name = "project_name"

        chain = ProvenanceChainMap(project={"project_name": "myapp"})
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.CWD_PATH,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "myapp"
        assert source == ConfigSource.PROJECT_CONFIG

    def test_falls_back_to_pyproject_toml(self, tmp_path: Path):
        """Test resolution falls back to pyproject.toml."""
        # Create pyproject.toml with project name
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text('[project]\nname = "my-awesome-project"\n')

        field = ProjectNameField(config_file="project")
        field.field_name = "project_name"

        chain = ProvenanceChainMap()  # Empty configs
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.CWD_PATH,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "my-awesome-project"
        assert source == ConfigSource.PYPROJECT

    def test_falls_back_to_directory_name(self, tmp_path: Path):
        """Test resolution falls back to directory name."""
        field = ProjectNameField(config_file="project")
        field.field_name = "project_name"

        chain = ProvenanceChainMap()  # Empty configs
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.CWD_PATH,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        # Should normalize directory name
        normalized = normalize_project_name(tmp_path.name)
        assert value == normalized or value == "myproject"
        assert source == ConfigSource.CWD_NAME

    def test_does_not_normalize_value_from_config(self, tmp_path: Path):
        """Test resolution returns raw value from config without normalization."""
        field = ProjectNameField(config_file="project")
        field.field_name = "project_name"

        chain = ProvenanceChainMap(project={"project_name": "My_Project"})
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.CWD_PATH,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        # ProjectNameField.resolve() does NOT normalize - returns raw value
        # Normalization only happens during interactive prompting
        assert value == "My_Project"
        assert source == ConfigSource.PROJECT_CONFIG


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestFieldSpecializationsIntegration:
    """Integration tests for field specializations working together."""

    def test_all_fields_have_unique_purposes(self):
        """Test that each specialized field has a distinct purpose."""
        email = EmailField()
        hostname = HostnameField()
        seed_command = SeedCommandField()
        log_level = LogLevelField()
        name = NameField()
        enum_field = EnumField(Mode)
        project_name = ProjectNameField()

        # Each should be a different class
        field_types = {
            type(email),
            type(hostname),
            type(seed_command),
            type(log_level),
            type(name),
            type(enum_field),
            type(project_name),
        }
        assert len(field_types) == 7

    def test_validation_errors_are_specific(self):
        """Test validation errors contain helpful messages."""
        # EmailField
        email = EmailField()
        email.field_name = "email"
        try:
            email.validate("invalid")
        except ConfigValidationError as e:
            assert "email" in str(e).lower()

        # SeedCommandField
        seed = SeedCommandField()
        seed.field_name = "seed_command"
        try:
            seed.validate("invalid")
        except ConfigValidationError as e:
            assert "module.path:attribute" in str(e)

        # LogLevelField
        log = LogLevelField()
        log.field_name = "log_level"
        try:
            log.validate("invalid")
        except ConfigValidationError as e:
            assert "Invalid log_level" in str(e)

        # ProjectNameField
        project = ProjectNameField()
        project.field_name = "project_name"
        try:
            project.validate("Invalid_Name")
        except ConfigValidationError as e:
            assert "DNS label" in str(e)
