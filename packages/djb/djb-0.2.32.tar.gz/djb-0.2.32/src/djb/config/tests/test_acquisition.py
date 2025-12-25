"""Tests for djb.config.acquisition module; field acquisition and external sources."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import attrs
import pytest

from djb.config.acquisition import (
    AcquisitionContext,
    AcquisitionResult,
    ExternalSource,
    GitConfigSource,
    _is_acquirable,
    _save_field_value,
    acquire_all_fields,
)
from djb.config.constants import ATTRSLIB_METADATA_KEY
from djb.config.file import LOCAL, PROJECT, load_config
from djb.config.resolution import ConfigSource
from djb.config.tests import TestDjbConfigBase


class TestAcquisitionContext:
    """Tests for AcquisitionContext dataclass."""

    def test_creation(self, tmp_path: Path):
        """Test AcquisitionContext can be created."""
        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value="test-value",
            source=ConfigSource.LOCAL_CONFIG,
            other_values={"name": "John"},
        )

        assert ctx.project_root == tmp_path
        assert ctx.current_value == "test-value"
        assert ctx.source == ConfigSource.LOCAL_CONFIG
        assert ctx.other_values == {"name": "John"}

    def test_is_explicit_with_explicit_source(self, tmp_path: Path):
        """Test is_explicit() returns True for explicit sources."""
        for source in [
            ConfigSource.CLI,
            ConfigSource.ENV,
            ConfigSource.LOCAL_CONFIG,
            ConfigSource.PROJECT_CONFIG,
        ]:
            ctx = AcquisitionContext(
                project_root=tmp_path,
                current_value="val",
                source=source,
                other_values={},
            )
            assert ctx.is_explicit() is True

    def test_is_explicit_with_derived_source(self, tmp_path: Path):
        """Test is_explicit() returns False for derived sources."""
        for source in [
            ConfigSource.PYPROJECT,
            ConfigSource.GIT,
            ConfigSource.CWD_NAME,
            ConfigSource.CWD_PATH,
            ConfigSource.DEFAULT,
            ConfigSource.DERIVED,
        ]:
            ctx = AcquisitionContext(
                project_root=tmp_path,
                current_value="val",
                source=source,
                other_values={},
            )
            assert ctx.is_explicit() is False

    def test_is_explicit_with_none_source(self, tmp_path: Path):
        """Test is_explicit() returns False when source is None."""
        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )
        assert ctx.is_explicit() is False

    def test_is_derived_with_derived_source(self, tmp_path: Path):
        """Test is_derived() returns True for derived sources."""
        for source in [
            ConfigSource.PYPROJECT,
            ConfigSource.GIT,
            ConfigSource.CWD_NAME,
            ConfigSource.CWD_PATH,
            ConfigSource.DEFAULT,
            ConfigSource.DERIVED,
        ]:
            ctx = AcquisitionContext(
                project_root=tmp_path,
                current_value="val",
                source=source,
                other_values={},
            )
            assert ctx.is_derived() is True

    def test_is_derived_with_explicit_source(self, tmp_path: Path):
        """Test is_derived() returns False for explicit sources."""
        for source in [
            ConfigSource.CLI,
            ConfigSource.ENV,
            ConfigSource.LOCAL_CONFIG,
            ConfigSource.PROJECT_CONFIG,
        ]:
            ctx = AcquisitionContext(
                project_root=tmp_path,
                current_value="val",
                source=source,
                other_values={},
            )
            assert ctx.is_derived() is False

    def test_is_derived_with_none_source(self, tmp_path: Path):
        """Test is_derived() returns False when source is None."""
        ctx = AcquisitionContext(
            project_root=tmp_path,
            current_value=None,
            source=None,
            other_values={},
        )
        assert ctx.is_derived() is False


class TestAcquisitionResult:
    """Tests for AcquisitionResult dataclass."""

    def test_creation_with_defaults(self):
        """Test AcquisitionResult can be created with defaults."""
        result = AcquisitionResult(value="test-value")

        assert result.value == "test-value"
        assert result.should_save is True
        assert result.source_name is None
        assert result.was_prompted is False

    def test_creation_with_all_fields(self):
        """Test AcquisitionResult can be created with all fields."""
        result = AcquisitionResult(
            value="test@example.com",
            should_save=False,
            source_name="git config",
            was_prompted=True,
        )

        assert result.value == "test@example.com"
        assert result.should_save is False
        assert result.source_name == "git config"
        assert result.was_prompted is True


class TestGitConfigSource:
    """Tests for GitConfigSource external source."""

    def test_name_property(self):
        """Test GitConfigSource.name returns 'git config'."""
        source = GitConfigSource(key="user.email")
        assert source.name == "git config"

    def test_get_returns_value_on_success(self):
        """Test GitConfigSource.get() returns value when git config succeeds."""
        source = GitConfigSource(key="user.email")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="test@example.com\n")
            result = source.get()

        assert result == "test@example.com"
        mock_run.assert_called_once_with(
            ["git", "config", "--get", "user.email"],
            capture_output=True,
            text=True,
        )

    def test_get_returns_none_on_nonzero_exit(self):
        """Test GitConfigSource.get() returns None when git config fails."""
        source = GitConfigSource(key="user.nonexistent")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = source.get()

        assert result is None

    def test_get_returns_none_on_file_not_found(self):
        """Test GitConfigSource.get() returns None when git is not installed."""
        source = GitConfigSource(key="user.email")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            result = source.get()

        assert result is None

    def test_get_returns_none_on_os_error(self):
        """Test GitConfigSource.get() returns None on OSError."""
        source = GitConfigSource(key="user.email")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = OSError("Some OS error")
            result = source.get()

        assert result is None

    def test_get_returns_none_on_empty_output(self):
        """Test GitConfigSource.get() returns None on empty stdout."""
        source = GitConfigSource(key="user.email")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = source.get()

        assert result is None

    def test_get_strips_whitespace(self):
        """Test GitConfigSource.get() strips whitespace from output."""
        source = GitConfigSource(key="user.name")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="  John Doe  \n")
            result = source.get()

        assert result == "John Doe"

    def test_conforms_to_external_source_protocol(self):
        """Test GitConfigSource conforms to ExternalSource protocol."""
        source = GitConfigSource(key="user.email")
        assert isinstance(source, ExternalSource)


class TestIsAcquirable:
    """Tests for _is_acquirable helper function."""

    def test_acquirable_field_with_acquire_and_prompt_text(self):
        """Test _is_acquirable returns True for field with acquire() and prompt_text."""
        field = MagicMock()
        field.prompt_text = "Enter value"

        assert _is_acquirable(field) is True

    def test_not_acquirable_without_prompt_text(self):
        """Test _is_acquirable returns False when prompt_text is None."""
        field = MagicMock()
        field.prompt_text = None

        assert _is_acquirable(field) is False

    def test_not_acquirable_without_acquire_method(self):
        """Test _is_acquirable returns False when acquire() doesn't exist."""
        field = MagicMock(spec=["prompt_text"])
        field.prompt_text = "Enter value"

        assert _is_acquirable(field) is False


class TestSaveFieldValue:
    """Tests for _save_field_value helper function."""

    def test_saves_to_local_config(self, tmp_path: Path):
        """Test _save_field_value saves to local.yaml for local config_file."""
        field = MagicMock()
        field.config_file = "local"
        field.config_file_key = "name"
        field.field_name = "name"

        _save_field_value(field, "John", tmp_path)

        config = load_config(LOCAL, tmp_path)
        assert config == {"name": "John"}

    def test_saves_to_project_config(self, tmp_path: Path):
        """Test _save_field_value saves to project.yaml for project config_file."""
        field = MagicMock()
        field.config_file = "project"
        field.config_file_key = "hostname"
        field.field_name = "hostname"

        _save_field_value(field, "example.com", tmp_path)

        config = load_config(PROJECT, tmp_path)
        assert config == {"hostname": "example.com"}

    def test_derives_key_from_field_name(self, tmp_path: Path):
        """Test _save_field_value uses field_name when config_file_key is None."""
        field = MagicMock()
        field.config_file = "local"
        field.config_file_key = None
        field.field_name = "email"

        _save_field_value(field, "test@example.com", tmp_path)

        config = load_config(LOCAL, tmp_path)
        assert config == {"email": "test@example.com"}

    def test_merges_with_existing_config(self, tmp_path: Path):
        """Test _save_field_value merges with existing config."""
        # Create existing config
        config_dir = tmp_path / ".djb"
        config_dir.mkdir()
        (config_dir / "local.yaml").write_text("existing: value\n")

        field = MagicMock()
        field.config_file = "local"
        field.config_file_key = "name"
        field.field_name = "name"

        _save_field_value(field, "John", tmp_path)

        config = load_config(LOCAL, tmp_path)
        assert config == {"existing": "value", "name": "John"}

    def test_treats_none_config_file_as_project(self, tmp_path: Path):
        """Test _save_field_value treats None config_file as project."""
        field = MagicMock()
        field.config_file = None
        field.config_file_key = "key"
        field.field_name = "key"

        _save_field_value(field, "value", tmp_path)

        config = load_config(PROJECT, tmp_path)
        assert config == {"key": "value"}


class TestAcquireAllFields:
    """Tests for acquire_all_fields generator function."""

    def test_skips_fields_without_config_field_metadata(self, tmp_path: Path):
        """Test acquire_all_fields skips fields without ConfigField metadata."""

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            regular_field: str = "default"

        config = TestConfig()

        results = list(acquire_all_fields(tmp_path, config))
        assert results == []

    def test_skips_non_acquirable_fields(self, tmp_path: Path):
        """Test acquire_all_fields skips fields without prompt_text."""
        mock_field = MagicMock()
        mock_field.prompt_text = None  # Not acquirable

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default="default",
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig()

        results = list(acquire_all_fields(tmp_path, config))
        assert results == []

    def test_skips_explicit_fields(self, tmp_path: Path):
        """Test acquire_all_fields skips fields with explicit sources."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default="John",
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig(_provenance={"name": ConfigSource.LOCAL_CONFIG})

        results = list(acquire_all_fields(tmp_path, config))
        assert results == []

    def test_calls_acquire_for_acquirable_field(self, tmp_path: Path):
        """Test acquire_all_fields calls acquire() for acquirable fields."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None
        mock_field.config_file = "local"
        mock_field.config_file_key = "name"
        mock_field.acquire.return_value = AcquisitionResult(
            value="John",
            should_save=True,
            source_name=None,
            was_prompted=True,
        )

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig(_provenance={"name": ConfigSource.DERIVED})

        results = list(acquire_all_fields(tmp_path, config))

        assert len(results) == 1
        field_name, result = results[0]
        assert field_name == "name"
        assert result.value == "John"
        assert result.was_prompted is True
        mock_field.acquire.assert_called_once()

    def test_skips_when_acquire_returns_none(self, tmp_path: Path):
        """Test acquire_all_fields skips field when acquire() returns None."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None
        mock_field.acquire.return_value = None  # Acquisition cancelled

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig()

        results = list(acquire_all_fields(tmp_path, config))
        assert results == []

    def test_saves_value_when_should_save_is_true(self, tmp_path: Path):
        """Test acquire_all_fields saves value when should_save=True."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None
        mock_field.config_file = "local"
        mock_field.config_file_key = "name"
        mock_field.acquire.return_value = AcquisitionResult(
            value="John",
            should_save=True,
        )

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig()

        list(acquire_all_fields(tmp_path, config))

        # Verify config was saved
        config_data = load_config(LOCAL, tmp_path)
        assert config_data == {"name": "John"}

    def test_does_not_save_when_should_save_is_false(self, tmp_path: Path):
        """Test acquire_all_fields doesn't save when should_save=False."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None
        mock_field.acquire.return_value = AcquisitionResult(
            value="John",
            should_save=False,
        )

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig()

        list(acquire_all_fields(tmp_path, config))

        # Verify config was NOT saved
        config_data = load_config(LOCAL, tmp_path)
        assert config_data == {}

    def test_does_not_save_none_values(self, tmp_path: Path):
        """Test acquire_all_fields doesn't save None values even with should_save=True."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None
        mock_field.acquire.return_value = AcquisitionResult(
            value=None,
            should_save=True,
        )

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig()

        list(acquire_all_fields(tmp_path, config))

        # Verify config was NOT saved (None values are not saved)
        config_data = load_config(LOCAL, tmp_path)
        assert config_data == {}

    def test_passes_other_values_to_context(self, tmp_path: Path):
        """Test acquire_all_fields passes previously configured values in context."""
        mock_field1 = MagicMock()
        mock_field1.prompt_text = "Enter name"
        mock_field1.field_name = None
        mock_field1.config_file = "local"
        mock_field1.config_file_key = "name"
        mock_field1.acquire.return_value = AcquisitionResult(value="John", should_save=True)

        mock_field2 = MagicMock()
        mock_field2.prompt_text = "Enter email"
        mock_field2.field_name = None
        mock_field2.config_file = "local"
        mock_field2.config_file_key = "email"

        # Capture the context passed to the second field's acquire()
        captured_ctx = None

        def capture_ctx(ctx: AcquisitionContext) -> AcquisitionResult:
            nonlocal captured_ctx
            captured_ctx = ctx
            return AcquisitionResult(value="john@example.com", should_save=True)

        mock_field2.acquire.side_effect = capture_ctx

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field1},
            )
            email: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field2},
            )

        config = TestConfig()

        list(acquire_all_fields(tmp_path, config))

        # Second field should have received first field's value in other_values
        assert captured_ctx is not None
        assert captured_ctx.other_values == {"name": "John"}

    def test_sets_field_name_on_config_field(self, tmp_path: Path):
        """Test acquire_all_fields sets field_name on ConfigField."""
        mock_field = MagicMock()
        mock_field.prompt_text = "Enter name"
        mock_field.field_name = None
        mock_field.config_file = "local"
        mock_field.config_file_key = "name"
        mock_field.acquire.return_value = AcquisitionResult(value="John", should_save=True)

        @attrs.frozen
        class TestConfig(TestDjbConfigBase):
            my_field_name: str = attrs.field(
                default=None,
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = TestConfig()

        list(acquire_all_fields(tmp_path, config))

        # Verify field_name was set
        assert mock_field.field_name == "my_field_name"
