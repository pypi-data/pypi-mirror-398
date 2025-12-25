"""Tests for djb.config.field module - ConfigFieldABC and StringField."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import attrs
import pytest

from djb.config.acquisition import AcquisitionContext, AcquisitionResult, ExternalSource
from djb.config.constants import ATTRSLIB_METADATA_KEY
from djb.config.field import ConfigFieldABC, ConfigValidationError, StringField
from djb.config.prompting import PromptResult
from djb.config.resolution import ConfigSource, ProvenanceChainMap, ResolutionContext, _NOT_LOADED


class TestConfigValidationError:
    """Tests for ConfigValidationError exception."""

    def test_is_exception(self):
        """Test ConfigValidationError is an Exception."""
        error = ConfigValidationError("invalid value")
        assert isinstance(error, Exception)

    def test_message_is_preserved(self):
        """Test error message is preserved."""
        error = ConfigValidationError("expected: user@domain.com")
        assert str(error) == "expected: user@domain.com"


class TestConfigFieldABCInit:
    """Tests for ConfigFieldABC.__init__()."""

    def test_default_values(self):
        """Test ConfigFieldABC can be created with default values."""
        field = StringField()

        assert field._env_key is None
        assert field._config_file_key is None
        assert field.config_file is None
        assert field.default is attrs.NOTHING
        assert field.prompt_text is None
        assert field.validation_hint is None
        assert field.external_sources == []

    def test_explicit_values(self):
        """Test ConfigFieldABC can be created with explicit values."""

        class MockSource:
            @property
            def name(self) -> str:
                return "test"

            def get(self) -> str | None:
                return None

        sources: list[ExternalSource] = [MockSource()]
        field = StringField(
            env_key="DJB_CUSTOM_EMAIL",
            config_file_key="email_address",
            config_file="local",
            default="default@example.com",
            prompt_text="Enter email",
            validation_hint="expected: user@domain.com",
            external_sources=sources,
        )

        assert field._env_key == "DJB_CUSTOM_EMAIL"
        assert field._config_file_key == "email_address"
        assert field.config_file == "local"
        assert field.default == "default@example.com"
        assert field.prompt_text == "Enter email"
        assert field.validation_hint == "expected: user@domain.com"
        assert field.external_sources == sources


class TestConfigFieldABCEnvKey:
    """Tests for ConfigFieldABC.env_key property."""

    def test_returns_explicit_env_key(self):
        """Test env_key returns explicitly set value."""
        field = StringField(env_key="DJB_CUSTOM")
        assert field.env_key == "DJB_CUSTOM"

    def test_derives_from_field_name(self):
        """Test env_key derives from field_name when not set."""
        field = StringField()
        field.field_name = "email"
        assert field.env_key == "DJB_EMAIL"

    def test_derives_uppercase(self):
        """Test derived env_key is uppercase."""
        field = StringField()
        field.field_name = "project_name"
        assert field.env_key == "DJB_PROJECT_NAME"

    def test_returns_none_when_field_name_not_set(self):
        """Test env_key returns None when field_name is not set."""
        field = StringField()
        assert field.field_name is None
        assert field.env_key is None


class TestConfigFieldABCConfigFileKey:
    """Tests for ConfigFieldABC.config_file_key property."""

    def test_returns_explicit_config_file_key(self):
        """Test config_file_key returns explicitly set value."""
        field = StringField(config_file_key="email_address")
        assert field.config_file_key == "email_address"

    def test_derives_from_field_name(self):
        """Test config_file_key derives from field_name when not set."""
        field = StringField()
        field.field_name = "email"
        assert field.config_file_key == "email"

    def test_returns_none_when_field_name_not_set(self):
        """Test config_file_key returns None when field_name is not set."""
        field = StringField()
        assert field.config_file_key is None


class TestConfigFieldABCDisplayName:
    """Tests for ConfigFieldABC.display_name property."""

    def test_converts_underscores_to_spaces(self):
        """Test display_name converts underscores to spaces."""
        field = StringField()
        field.field_name = "project_name"
        assert field.display_name == "Project Name"

    def test_title_cases(self):
        """Test display_name title cases the result."""
        field = StringField()
        field.field_name = "email"
        assert field.display_name == "Email"

    def test_default_for_no_field_name(self):
        """Test display_name defaults to 'Field' when field_name not set."""
        field = StringField()
        assert field.display_name == "Field"


class TestConfigFieldABCCall:
    """Tests for ConfigFieldABC.__call__() method."""

    def test_returns_attrs_field(self):
        """Test __call__ returns an attrs.field()."""
        config_field = StringField()
        result = config_field()

        # Result should be usable as an attrs field
        assert hasattr(result, "metadata")
        assert ATTRSLIB_METADATA_KEY in result.metadata

    def test_metadata_contains_config_field(self):
        """Test attrs field metadata contains the ConfigField."""
        config_field = StringField()
        result = config_field()

        assert result.metadata[ATTRSLIB_METADATA_KEY] is config_field

    def test_factory_returns_not_loaded_sentinel(self):
        """Test attrs field factory returns _NOT_LOADED sentinel."""
        config_field = StringField()

        @attrs.define
        class TestConfig:
            value: str = config_field()

        # When instantiated without arguments, the factory returns _NOT_LOADED
        instance = TestConfig()
        assert instance.value is _NOT_LOADED


class TestConfigFieldABCResolve:
    """Tests for ConfigFieldABC.resolve() method."""

    def test_resolves_from_configs(self, tmp_path: Path):
        """Test resolve() returns value from config layers."""
        field = StringField()
        field.field_name = "name"

        chain = ProvenanceChainMap(local={"name": "John"})
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "John"
        assert source == ConfigSource.LOCAL_CONFIG

    def test_resolves_from_env(self, tmp_path: Path):
        """Test resolve() returns value from env layer with env_key."""
        field = StringField()
        field.field_name = "email"

        chain = ProvenanceChainMap(env={"DJB_EMAIL": "test@example.com"})
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "test@example.com"
        assert source == ConfigSource.ENV

    def test_resolves_to_default(self, tmp_path: Path):
        """Test resolve() returns default when not in configs."""
        field = StringField(default="default-value")
        field.field_name = "name"

        chain = ProvenanceChainMap()
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "default-value"
        assert source == ConfigSource.DEFAULT

    def test_resolves_to_none_no_default(self, tmp_path: Path):
        """Test resolve() returns (None, None) when no value and no default."""
        field = StringField()
        field.field_name = "optional"

        chain = ProvenanceChainMap()
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value is None
        assert source is None

    def test_applies_normalizer(self, tmp_path: Path):
        """Test resolve() applies normalize() to resolved value."""

        class LowercaseField(ConfigFieldABC):
            def normalize(self, value):
                return value.lower() if isinstance(value, str) else value

        field = LowercaseField()
        field.field_name = "name"

        chain = ProvenanceChainMap(local={"name": "JOHN"})
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "john"

    def test_respects_priority(self, tmp_path: Path):
        """Test resolve() respects cli > env > local > project priority."""
        field = StringField()
        field.field_name = "name"

        chain = ProvenanceChainMap(
            cli={"name": "cli-value"},
            env={"DJB_NAME": "env-value"},
            local={"name": "local-value"},
            project={"name": "project-value"},
        )
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        value, source = field.resolve(ctx)
        assert value == "cli-value"
        assert source == ConfigSource.CLI


class TestConfigFieldABCNormalize:
    """Tests for ConfigFieldABC.normalize() method."""

    def test_default_is_identity(self):
        """Test default normalize() returns value unchanged."""
        field = StringField()
        assert field.normalize("test") == "test"
        assert field.normalize(123) == 123
        assert field.normalize(None) is None


class TestConfigFieldABCValidate:
    """Tests for ConfigFieldABC.validate() method."""

    def test_default_is_noop(self):
        """Test default validate() does nothing."""
        field = StringField()
        # Should not raise
        field.validate("anything")
        field.validate(123)
        field.validate(None)


class TestConfigFieldABCGetDefault:
    """Tests for ConfigFieldABC.get_default() method."""

    def test_returns_default_value(self):
        """Test get_default() returns the default."""
        field = StringField(default="my-default")
        assert field.get_default() == "my-default"

    def test_returns_none_when_nothing(self):
        """Test get_default() returns None when default is NOTHING."""
        field = StringField()  # No default
        assert field.get_default() is None


class TestConfigFieldABCIsValid:
    """Tests for ConfigFieldABC._is_valid() method."""

    def test_returns_true_when_valid(self):
        """Test _is_valid returns True when validate() doesn't raise."""
        field = StringField()
        assert field._is_valid("anything") is True

    def test_returns_false_when_validation_error(self):
        """Test _is_valid returns False when validate() raises ConfigValidationError."""

        class AlwaysInvalidField(ConfigFieldABC):
            def validate(self, value):
                raise ConfigValidationError("always invalid")

        field = AlwaysInvalidField()
        assert field._is_valid("anything") is False

    def test_returns_false_when_value_error(self):
        """Test _is_valid returns False when validate() raises ValueError."""

        class ValueErrorField(ConfigFieldABC):
            def validate(self, value):
                raise ValueError("bad value")

        field = ValueErrorField()
        assert field._is_valid("anything") is False

    def test_returns_false_when_type_error(self):
        """Test _is_valid returns False when validate() raises TypeError."""

        class TypeErrorField(ConfigFieldABC):
            def validate(self, value):
                raise TypeError("bad type")

        field = TypeErrorField()
        assert field._is_valid("anything") is False


class TestConfigFieldABCRequireString:
    """Tests for ConfigFieldABC._require_string() method."""

    def test_returns_true_for_string(self):
        """Test _require_string returns True for string values."""
        field = StringField()
        field.field_name = "test"
        assert field._require_string("hello") is True

    def test_returns_false_for_none_when_allowed(self):
        """Test _require_string returns False for None when allow_none=True."""
        field = StringField()
        field.field_name = "test"
        assert field._require_string(None) is False

    def test_raises_for_none_when_not_allowed(self):
        """Test _require_string raises for None when allow_none=False."""
        field = StringField()
        field.field_name = "test"

        with pytest.raises(ConfigValidationError, match="test is required"):
            field._require_string(None, allow_none=False)

    def test_raises_for_non_string(self):
        """Test _require_string raises for non-string values."""
        field = StringField()
        field.field_name = "test"

        with pytest.raises(ConfigValidationError, match="test must be a string.*int"):
            field._require_string(123)

        with pytest.raises(ConfigValidationError, match="test must be a string.*list"):
            field._require_string([])


class TestConfigFieldABCPromptedResult:
    """Tests for ConfigFieldABC._prompted_result() method."""

    def test_creates_acquisition_result(self):
        """Test _prompted_result creates correct AcquisitionResult."""
        field = StringField()
        field.field_name = "name"

        with patch("djb.config.field.logger"):
            result = field._prompted_result("John")

        assert isinstance(result, AcquisitionResult)
        assert result.value == "John"
        assert result.should_save is True
        assert result.source_name is None
        assert result.was_prompted is True

    def test_logs_done_message(self):
        """Test _prompted_result logs done message."""
        field = StringField()
        field.field_name = "email"

        with patch("djb.config.field.logger") as mock_logger:
            field._prompted_result("test@example.com")

        mock_logger.done.assert_called_once()
        call_args = mock_logger.done.call_args[0][0]
        assert "Email" in call_args
        assert "test@example.com" in call_args


class TestConfigFieldABCAcquire:
    """Tests for ConfigFieldABC.acquire() method."""

    def test_acquire_from_external_source(self, tmp_path: Path):
        """Test acquire() returns value from external source."""

        class MockSource:
            @property
            def name(self) -> str:
                return "mock source"

            def get(self) -> str | None:
                return "external-value"

        field = StringField(
            prompt_text="Enter value",
            external_sources=[MockSource()],
        )
        field.field_name = "name"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )

        result = field.acquire(ctx)

        assert result is not None
        assert result.value == "external-value"
        assert result.source_name == "mock source"
        assert result.was_prompted is False

    def test_acquire_skips_invalid_external_source(self, tmp_path: Path):
        """Test acquire() skips external source if value is invalid."""

        class MockSource:
            @property
            def name(self) -> str:
                return "mock source"

            def get(self) -> str | None:
                return "invalid"

        class ValidatingField(StringField):
            def validate(self, value):
                if value == "invalid":
                    raise ConfigValidationError("invalid value")

        field = ValidatingField(
            prompt_text="Enter value",
            external_sources=[MockSource()],
        )
        field.field_name = "name"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )

        # Should fall through to prompting
        with patch("djb.config.field.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(value="valid", source="user", attempts=1)
            with patch("djb.config.field.logger"):
                result = field.acquire(ctx)

        assert result is not None
        assert result.value == "valid"
        assert result.was_prompted is True

    def test_acquire_prompts_user(self, tmp_path: Path):
        """Test acquire() prompts user when no external sources."""
        field = StringField(
            prompt_text="Enter your name",
            validation_hint="letters only",
        )
        field.field_name = "name"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value="default-name",
            source=ConfigSource.DEFAULT,
            other_values={},
        )

        with patch("djb.config.field.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(value="John", source="user", attempts=1)
            with patch("djb.config.field.logger"):
                result = field.acquire(ctx)

        mock_prompt.assert_called_once()
        call_kwargs = mock_prompt.call_args
        assert call_kwargs[0][0] == "Enter your name"
        assert call_kwargs[1]["default"] == "default-name"
        assert call_kwargs[1]["validation_hint"] == "letters only"

        assert result is not None
        assert result.value == "John"
        assert result.was_prompted is True

    def test_acquire_returns_none_on_cancel(self, tmp_path: Path):
        """Test acquire() returns None when user cancels prompt."""
        field = StringField(prompt_text="Enter value")
        field.field_name = "name"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )

        with patch("djb.config.field.prompt") as mock_prompt:
            mock_prompt.return_value = PromptResult(value=None, source="cancelled", attempts=3)
            result = field.acquire(ctx)

        assert result is None

    def test_acquire_returns_current_value_when_no_prompt_text(self, tmp_path: Path):
        """Test acquire() returns current value when prompt_text not set."""
        field = StringField()  # No prompt_text
        field.field_name = "name"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value="existing-value",
            source=ConfigSource.DEFAULT,
            other_values={},
        )

        result = field.acquire(ctx)

        assert result is not None
        assert result.value == "existing-value"
        assert result.should_save is False
        assert result.was_prompted is False

    def test_acquire_returns_none_when_no_prompt_text_and_no_value(self, tmp_path: Path):
        """Test acquire() returns None when no prompt_text and no current value."""
        field = StringField()  # No prompt_text
        field.field_name = "name"

        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )

        result = field.acquire(ctx)
        assert result is None


class TestConfigFieldABCAttrsValidator:
    """Tests for ConfigFieldABC._attrs_validator() static method."""

    def test_skips_not_loaded_sentinel(self):
        """Test _attrs_validator skips _NOT_LOADED sentinel."""
        mock_attrib = MagicMock()
        mock_attrib.metadata = {ATTRSLIB_METADATA_KEY: StringField()}

        # Should not raise
        ConfigFieldABC._attrs_validator(None, mock_attrib, _NOT_LOADED)

    def test_calls_validate_on_field(self):
        """Test _attrs_validator calls validate() on the config field."""

        class AlwaysInvalidField(ConfigFieldABC):
            def validate(self, value):
                raise ConfigValidationError("always invalid")

        field = AlwaysInvalidField()
        mock_attrib = MagicMock()
        mock_attrib.name = "test_field"
        mock_attrib.metadata = {ATTRSLIB_METADATA_KEY: field}

        with pytest.raises(ConfigValidationError, match="always invalid"):
            ConfigFieldABC._attrs_validator(None, mock_attrib, "some-value")

    def test_skips_when_no_config_field_in_metadata(self):
        """Test _attrs_validator does nothing when no ConfigField in metadata."""
        mock_attrib = MagicMock()
        mock_attrib.metadata = {}

        # Should not raise
        ConfigFieldABC._attrs_validator(None, mock_attrib, "some-value")

    def test_sets_field_name_from_attrib(self):
        """Test _attrs_validator sets field_name from attribute name."""
        field = StringField()
        mock_attrib = MagicMock()
        mock_attrib.name = "my_custom_field"
        mock_attrib.metadata = {ATTRSLIB_METADATA_KEY: field}

        ConfigFieldABC._attrs_validator(None, mock_attrib, "some-value")

        assert field.field_name == "my_custom_field"


class TestStringField:
    """Tests for StringField class."""

    def test_is_subclass_of_config_field_abc(self):
        """Test StringField is a subclass of ConfigFieldABC."""
        assert issubclass(StringField, ConfigFieldABC)

    def test_has_no_custom_behavior(self):
        """Test StringField has no custom overrides."""
        field = StringField()

        # Should use base class behavior
        assert field.normalize("test") == "test"
        # Should not raise on validate
        field.validate("anything")

    def test_can_be_used_as_field(self):
        """Test StringField can be used to define an attrs field."""
        field = StringField(default="default-value")

        @attrs.define
        class TestConfig:
            name: str = field()

        # Verify the field works
        config = TestConfig()
        assert config.name is _NOT_LOADED  # Factory returns sentinel
